from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from datetime import datetime
from .models import Account, Transaction
from .serializers import AccountSerializer, TransactionSerializer
from .services import TransactionService

class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own accounts
        return Account.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Automatically assign the current user when creating an account
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """List all transactions for a specific account"""
        try:
            # Get filter parameters
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            transaction_type = request.query_params.get('type')
            
            # Convert string dates to datetime if provided
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                # Set to end of day
                end_date = end_date.replace(hour=23, minute=59, second=59)
            
            transactions = TransactionService.get_account_transactions(
                pk, start_date, end_date, transaction_type
            )
            
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data)
            
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def deposit(self, request, pk=None):
        """Deposit funds to this account"""
        try:
            # Check if account belongs to the user
            account = self.get_object()
            
            amount = request.data.get('amount')
            description = request.data.get('description')
            
            transaction = TransactionService.deposit(
                account.id, amount, description
            )
            
            serializer = TransactionSerializer(transaction)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """Withdraw funds from this account"""
        try:
            # Check if account belongs to the user
            account = self.get_object()
            
            amount = request.data.get('amount')
            description = request.data.get('description')
            
            transaction = TransactionService.withdraw(
                account.id, amount, description
            )
            
            serializer = TransactionSerializer(transaction)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def transfer(self, request, pk=None):
        """Transfer funds to another account"""
        try:
            # Check if source account belongs to the user
            from_account = self.get_object()
            
            to_account_id = request.data.get('to_account')
            amount = request.data.get('amount')
            description = request.data.get('description')
            
            # Validate destination account
            try:
                to_account = Account.objects.get(id=to_account_id)
            except Account.DoesNotExist:
                return Response(
                    {"error": "Destination account not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            transaction = TransactionService.transfer(
                from_account.id, to_account.id, amount, description
            )
            
            serializer = TransactionSerializer(transaction)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
