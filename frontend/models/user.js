const mongoose = require("mongoose");

const userSchema = new mongoose.Schema({
  username: String,
  email: String,
  password: String,
  latitude: String,
  longitude: String,
  avg_power: String, // ✅ Added
});

module.exports = mongoose.model("User", userSchema);
