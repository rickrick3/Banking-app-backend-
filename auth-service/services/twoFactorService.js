// services/twoFactorService.js
const speakeasy = require('speakeasy');
const QRCode = require('qrcode');

exports.generateSecret = (email) => {
  return speakeasy.generateSecret({
    name: `SecuredBankingApp:${email}`
  });
};

exports.generateQRCode = async (otpauthUrl) => {
  try {
    return await QRCode.toDataURL(otpauthUrl);
  } catch (error) {
    throw new Error('Could not generate QR code');
  }
};

exports.verifyToken = (secret, token) => {
  return speakeasy.totp.verify({
    secret,
    encoding: 'base32',
    token
  });
};