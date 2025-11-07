const mongoose = require("mongoose");

const userSchema = new mongoose.Schema({
  username: String,
  email: String,
  password: String,
  latitude: Number,
  longitude: Number,
  avg_power: Number,
});

module.exports = mongoose.model("User", userSchema);
