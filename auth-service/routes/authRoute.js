// routes/authRoutes.js
const express = require('express');
const authController = require('../controllers/authController');
const { loginLimiter, resetPasswordLimiter } = require('../middleware/rateLimiter');
const { authenticateToken } = require('../middleware/auth');
const {
  registerValidation,
  loginValidation,
  passwordChangeValidation,
  passwordResetValidation
} = require('../middleware/validation');
const { handleValidationErrors } = require('../utils/errorHandler');

const router = express.Router();

// Public routes
router.post('/register', registerValidation, handleValidationErrors, authController.register);
router.post('/login', loginValidation, handleValidationErrors, loginLimiter, authController.login);
router.post('/verify-login-2fa', authController.verifyLoginTwoFactor);
router.post('/biometric-login', authController.biometricLogin);
router.post('/refresh-token', authController.refreshToken);
router.post('/forgot-password', authController.requestPasswordReset);
router.post('/reset-password', passwordResetValidation, handleValidationErrors, resetPasswordLimiter, authController.resetPassword);

// Protected routes
router.post('/setup-2fa', authenticateToken, authController.setupTwoFactor);
router.post('/verify-2fa', authenticateToken, authController.verifyTwoFactor);
router.post('/setup-biometric', authenticateToken, authController.setupBiometric);
router.post('/change-password', authenticateToken, passwordChangeValidation, handleValidationErrors, authController.changePassword);

module.exports = router;