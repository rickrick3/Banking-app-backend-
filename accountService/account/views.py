from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Account
from .serializers import AccountSerializer, AccountCreateSerializer, TopUpSerializer
import uuid
import requests
import os
import jwt
import datetime

class AccountListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Extract user_id from token
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = jwt.decode(token, os.getenv('SECRET_KEY', 'your-secret-key-here'), algorithms=['HS256'])
                user_id = payload.get('user_id')
                accounts = Account.objects.filter(user_id=user_id)
                serializer = AccountSerializer(accounts, many=True)
                return Response(serializer.data)
            except (jwt.DecodeError, Exception) as e:
                return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"error": "Invalid authorization header"}, status=status.HTTP_401_UNAUTHORIZED)

class AccountDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, account_id):
        try:
            account = Account.objects.get(id=account_id)
            
            # Verify user owns this account
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                try:
                    payload = jwt.decode(token, os.getenv('SECRET_KEY', 'your-secret-key-here'), algorithms=['HS256'])
                    user_id = payload.get('user_id')
                    if str(account.user_id) != user_id:
                        return Response({"error": "Not authorized to access this account"}, 
                                        status=status.HTTP_403_FORBIDDEN)
                    
                    serializer = AccountSerializer(account)
                    return Response(serializer.data)
                except jwt.DecodeError:
                    return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            return Response({"error": "Invalid authorization header"}, status=status.HTTP_401_UNAUTHORIZED)
            
        except Account.DoesNotExist:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

class AccountCreateView(APIView):
    def post(self, request):
        serializer = AccountCreateSerializer(data=request.data)
        if serializer.is_valid():
            account_data = {
                'user_id': serializer.validated_data['user_id'],
                'account_type': serializer.validated_data['account_type'],
                'currency': serializer.validated_data['currency'],
            }
            
            account_serializer = AccountSerializer(data=account_data)
            if account_serializer.is_valid():
                account = account_serializer.save()
                return Response(
                    {"message": "Account created successfully", "account": account_serializer.data},
                    status=status.HTTP_201_CREATED
                )
            return Response(account_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TopUpAccountView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = TopUpSerializer(data=request.data)
        if serializer.is_valid():
            account_id = serializer.validated_data['account_id']
            amount = serializer.validated_data['amount']
            description = serializer.validated_data.get('description', 'Account top-up')
            
            try:
                with transaction.atomic():
                    # Get the account
                    account = Account.objects.select_for_update().get(id=account_id)
                    
                    # Verify user owns this account
                    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
                    if auth_header.startswith('Bearer '):
                        token = auth_header.split(' ')[1]
                        try:
                            payload = jwt.decode(
                                token, 
                                os.getenv('SECRET_KEY', 'your-secret-key-here'), 
                                algorithms=['HS256']
                            )
                            user_id = payload.get('user_id')
                            if str(account.user_id) != user_id:
                                return Response(
                                    {"error": "Not authorized to top up this account"}, 
                                    status=status.HTTP_403_FORBIDDEN
                                )
                        except jwt.DecodeError:
                            return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
                    
                    # Check if account is active
                    if account.status != 'active':
                        return Response(
                            {"error": f"Cannot top up account with status: {account.status}"}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Update balance
                    account.balance += amount
                    account.save()
                    
                    # Record the transaction
                    transaction_service_url = os.getenv(
                        'TRANSACTION_SERVICE_URL', 
                        'http://transaction-service:8003'
                    )
                    try:
                        transaction_data = {
                            "account_id": str(account_id),
                            "transaction_type": "top_up",
                            "amount": float(amount),
                            "description": description,
                            "status": "completed"
                        }
                        requests.post(
                            f"{transaction_service_url}/api/transactions/",
                            json=transaction_data,
                            headers={"Authorization": request.META.get('HTTP_AUTHORIZATION', '')}
                        )
                    except Exception as e:
                        # Log the error but continue
                        print(f"Error recording transaction: {e}")
                    
                    return Response({
                        "message": "Account topped up successfully",
                        "new_balance": account.balance
                    })
                    
            except Account.DoesNotExist:
                return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)