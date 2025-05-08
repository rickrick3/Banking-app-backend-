const bcrypt = require('bcrypt');
const User = require('../libs/models/User');
const tokenService = require('../services/tokenService');
const twoFactorService = require('../services/twoFactorService');
const { asyncHandler } = require('../utils/errorHandler');

// Register new user
exports.register = asyncHandler(async (req, res) => {
  const { email, password, firstName, lastName, phoneNumber } = req.body;
  
  // Check if user already exists
  const existingUser = await User.findOne({ email });
  if (existingUser) {
    res.status(409);
    throw new Error('User already exists');
  }
  
  // Hash password
  const salt = await bcrypt.genSalt(10);
  const hashedPassword = await bcrypt.hash(password, salt);
  
  // Create new user
  const newUser = new User({
    email,
    password: hashedPassword,
    firstName,
    lastName,
    phoneNumber
  });
  
  await newUser.save();
  
  res.status(201).json({ message: 'User registered successfully' });
});

// Login user
exports.login = asyncHandler(async (req, res) => {
  const { email, password } = req.body;
  
  // Find user
  const user = await User.findOne({ email });
  if (!user) {
    res.status(401);
    throw new Error('Invalid credentials');
  }
  
  // Check if account is locked
  if (user.accountLocked) {
    res.status(403);
    throw new Error('Account locked. Please contact support.');
  }
  const isValidPassword = await bcrypt.compare(password, user.password);
  if (!isValidPassword) {
    // Increment failed login attempts
    user.failedLoginAttempts += 1;
    
    // Lock account after 5 failed attempts
    if (user.failedLoginAttempts >= 5) {
      user.accountLocked = true;
    }
    
    await user.save();
    
    res.status(401);
    throw new Error('Invalid credentials');
  }
  
  // If 2FA is enabled, return a temporary token for 2FA verification
  if (user.twoFactorEnabled) {
    const tempToken = tokenService.generateTempToken(user._id);
    return res.json({ tempToken, requiresSecondFactor: true });
  }
  
  // Reset failed login attempts
  user.failedLoginAttempts = 0;
  user.lastLogin = new Date();
  await user.save();
  
  // Generate JWT token
  const token = tokenService.generateToken(user._id, user.email);
  
  res.json({
    token,
    user: {
      id: user._id,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName
    }
  });
});

// Setup 2FA
exports.setupTwoFactor = asyncHandler(async (req, res) => {
  const { userId } = req.body;

  const user = await User.findById(userId);
  if (!user) {
    res.status(404);
    throw new Error('User not found');
  }
  
  // Generate new secret
  const secret = twoFactorService.generateSecret(user.email);
  
  // Save secret to user
  user.twoFactorSecret = secret.base32;
  await user.save();
  
  // Generate QR code
  const qrCode = await twoFactorService.generateQRCode(secret.otpauth_url);
  
  res.json({ secret: secret.base32, qrCode });
});

// Verify and enable 2FA
exports.verifyTwoFactor = asyncHandler(async (req, res) => {
  const { userId, token } = req.body;
  
  // Find user
  const user = await User.findById(userId);
  if (!user) {
    res.status(404);
    throw new Error('User not found');
  }
  
  // Verify token
  const verified = twoFactorService.verifyToken(user.twoFactorSecret, token);
  
  if (!verified) {
    res.status(401);
    throw new Error('Invalid 2FA token');
  }
  
  // Enable 2FA
  user.twoFactorEnabled = true;
  await user.save();
  
  res.json({ message: '2FA enabled successfully' });
});

// Verify 2FA during login
exports.verifyLoginTwoFactor = asyncHandler(async (req, res) => {
  const { tempToken, token } = req.body;
  
  // Verify temp token
  const decoded = tokenService.verifyToken(tempToken);
  if (!decoded.requiresSecondFactor) {
    res.status(401);
    throw new Error('Invalid token');
  }
  
  // Find user
  const user = await User.findById(decoded.id);
  if (!user) {
    res.status(404);
    throw new Error('User not found');
  }
  
  // Verify 2FA token
  const verified = twoFactorService.verifyToken(user.twoFactorSecret, token);
  
  if (!verified) {
    res.status(401);
    throw new Error('Invalid 2FA token');
  }
  
  // Reset failed login attempts
  user.failedLoginAttempts = 0;
  user.lastLogin = new Date();
  await user.save();
  
  // Generate full JWT token
  const fullToken = tokenService.generateToken(user._id, user.email);
  
  res.json({
    token: fullToken,
    user: {
      id: user._id,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName
    }
  });
});

// Setup biometric authentication
exports.setupBiometric = asyncHandler(async (req, res) => {
  const { userId, biometricData } = req.body;
  
  // Find user
  const user = await User.findById(userId);
  if (!user) {
    res.status(404);
    throw new Error('User not found');
  }
  
  // Store biometric data (in production this would be more secure)
  user.biometricData = biometricData;
  user.biometricEnabled = true;
  await user.save();
  
  res.json({ message: 'Biometric authentication enabled' });
});

// Biometric login
exports.biometricLogin = asyncHandler(async (req, res) => {
  const { biometricData } = req.body;
  
  // Find user with matching biometric data
  // In production, this would use a specialized biometric verification service
  const user = await User.findOne({ biometricData });
  if (!user) {
    res.status(401);
    throw new Error('Biometric verification failed');
  }
  
  // Update last login
  user.lastLogin = new Date();
  user.failedLoginAttempts = 0;
  await user.save();
  
  // Generate JWT token
  const token = tokenService.generateToken(user._id, user.email);
  
  res.json({
    token,
    user: {
      id: user._id,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName
    }
  });
});

// Refresh token
exports.refreshToken = asyncHandler(async (req, res) => {
  const { token } = req.body;
  
  // Verify existing token
  const decoded = tokenService.verifyTokenIgnoreExpiration(token);
  
  // Check if token is close to expiration (within 5 minutes)
  const currentTime = Math.floor(Date.now() / 1000);
  if (decoded.exp - currentTime > 300) {
    res.status(400);
    throw new Error('Token not eligible for refresh yet');
  }
  
  // Find user
  const user = await User.findById(decoded.id);
  if (!user) {
    res.status(404);
    throw new Error('User not found');
  }
  
  // Generate new token
  const newToken = tokenService.generateToken(user._id, user.email);
  
  res.json({ token: newToken });
});

// Change password
exports.changePassword = asyncHandler(async (req, res) => {
  const { userId, currentPassword, newPassword } = req.body;
  
  // Find user
  const user = await User.findById(userId);
  if (!user) {
    res.status(404);
    throw new Error('User not found');
  }
  
  // Verify current password
  const isValidPassword = await bcrypt.compare(currentPassword, user.password);
  if (!isValidPassword) {
    res.status(401);
    throw new Error('Current password is incorrect');
  }
  
  // Hash new password
  const salt = await bcrypt.genSalt(10);
  const hashedPassword = await bcrypt.hash(newPassword, salt);
  
  // Update password
  user.password = hashedPassword;
  user.updatedAt = new Date();
  await user.save();
  
  res.json({ message: 'Password changed successfully' });
});

// Request password reset
exports.requestPasswordReset = asyncHandler(async (req, res) => {
  const { email } = req.body;
  
  // Find user
  const user = await User.findOne({ email });
  
  // For security, don't reveal if email exists
  if (!user) {
    return res.json({ message: 'If your email is registered, you will receive a reset link' });
  }
  
  // Generate reset token
  const resetToken = tokenService.generateResetToken(user._id);
  
  // In production, send email with reset link
  
  res.json({
    message: 'If your email is registered, you will receive a reset link',
    resetToken // In production, this would only be sent via email
  });
});

// Reset password with token
exports.resetPassword = asyncHandler(async (req, res) => {
  const { resetToken, newPassword } = req.body;
  
  // Verify token
  const decoded = tokenService.verifyToken(resetToken);
  
  // Find user
  const user = await User.findById(decoded.id);
  if (!user) {
    res.status(404);
    throw new Error('User not found');
  }
  
  // Hash new password
  const salt = await bcrypt.genSalt(10);
  const hashedPassword = await bcrypt.hash(newPassword, salt);
  
  // Update password
  user.password = hashedPassword;
  user.updatedAt = new Date();
  user.failedLoginAttempts = 0;
  user.accountLocked = false;
  await user.save();
  
  res.json({ message: 'Password reset successfully' });
});