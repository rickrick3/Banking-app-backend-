// services/tokenService.js
const jwt = require('jsonwebtoken');

exports.generateToken = (userId, email, expiresIn = '1h') => {
  return jwt.sign(
    { id: userId, email },
    process.env.JWT_SECRET,
    { expiresIn }
  );
};

exports.generateTempToken = (userId, expiresIn = '5m') => {
  return jwt.sign(
    { id: userId, requiresSecondFactor: true },
    process.env.JWT_SECRET,
    { expiresIn }
  );
};

exports.generateResetToken = (userId, expiresIn = '15m') => {
  return jwt.sign(
    { id: userId },
    process.env.JWT_SECRET,
    { expiresIn }
  );
};

exports.verifyToken = (token) => {
  try {
    return jwt.verify(token, process.env.JWT_SECRET);
  } catch (error) {
    throw new Error('Invalid or expired token');
  }
};

exports.verifyTokenIgnoreExpiration = (token) => {
  try {
    return jwt.verify(token, process.env.JWT_SECRET, { ignoreExpiration: true });
  } catch (error) {
    throw new Error('Invalid token');
  }
};