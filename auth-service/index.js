// server.js
const express = require('express');
const dotenv = require('dotenv');
const connectDB = require('./config/db');
const authRoutes = require('./routes/authRoutes');
const { errorMiddleware } = require('./utils/errorHandler');

dotenv.config();
connectDB();

const app = express();
const PORT = process.env.PORT || 5003;

app.use(express.json());


app.use('/api/auth', authRoutes);
app.use(errorMiddleware);

app.listen(PORT, () => {
  console.log(`Auth service running on port ${PORT}`);
});