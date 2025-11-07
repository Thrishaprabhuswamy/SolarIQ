const express = require("express");
const mongoose = require("mongoose");
const bcrypt = require("bcryptjs");
const session = require("express-session");
const bodyParser = require("body-parser");
const axios = require("axios");
const User = require("./models/user");

const app = express();

// MongoDB setup
mongoose.connect("mongodb://127.0.0.1:27017/solarMonitor");
mongoose.connection.on("connected", () => console.log("✅ MongoDB connected"));

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static("public"));
app.set("view engine", "ejs");
app.use(
  session({
    secret: "solar_secret",
    resave: false,
    saveUninitialized: false,
  })
);

// accept JSON from frontend update requests
app.use(express.json());

// Authentication guard
function isAuth(req, res, next) {
  if (!req.session.user) return res.redirect("/login");
  next();
}

// Routes
app.get("/", (req, res) => res.redirect("/login"));
app.get("/login", (req, res) => res.render("login"));
app.get("/signup", (req, res) => res.render("signup"));

// Signup
app.post("/signup", async (req, res) => {
  try {
    const { username, email, password, confirmPassword, latitude, longitude, avg_power } = req.body;
    if (!username || !email || !password || password !== confirmPassword)
      return res.send("⚠️ Invalid or missing fields.");

    const exists = await User.findOne({ email });
    if (exists) return res.send("⚠️ Email already registered.");

    const hash = await bcrypt.hash(password, 10);
    const newUser = new User({ username, email, password: hash, latitude, longitude, avg_power });
    await newUser.save();

    res.redirect("/login");
  } catch (e) {
    console.error("❌ Signup error:", e);
    res.send("Error during signup.");
  }
});

// Login
app.post("/login", async (req, res) => {
  const { username, password } = req.body;
  const user = await User.findOne({ username });
  if (!user) return res.send("⚠️ User not found.");
  const match = await bcrypt.compare(password, user.password);
  if (!match) return res.send("⚠️ Wrong password.");
  req.session.user = user;
  res.redirect("/dashboard");
});

// Dashboard
app.get("/dashboard", isAuth, async (req, res) => {
  try {
    const [todayRes, historyRes] = await Promise.all([
      axios.get("http://127.0.0.1:5000/today_status"),
      axios.get("http://127.0.0.1:5000/history"),
    ]);

    res.render("dashboard", {
      user: req.session.user,
      avg_power: req.session.user ? req.session.user.avg_power : 0, // <-- pass avg_power explicitly
      todayData: todayRes.data || null,
      historyData: historyRes.data || [],
      forecastData: [], // keep frontend responsible for prediction fetch
    });
  } catch (err) {
    console.error("❌ Flask connection error:", err.message);
    res.render("dashboard", {
      user: req.session.user,
      avg_power: req.session.user ? req.session.user.avg_power : 0, // <-- keep available on error path
      todayData: null,
      historyData: [],
      forecastData: [], // ✅ always defined
    });
  }
});

// Logout
app.get("/logout", (req, res) => req.session.destroy(() => res.redirect("/login")));

// Start server
const PORT = 3000;
app.listen(PORT, () => console.log(`🚀 Node frontend on http://localhost:${PORT}`));

// Profile update endpoint (edit lat, lon, avg_power)
app.post("/profile/update", isAuth, async (req, res) => {
  try {
    const { latitude, longitude, avg_power } = req.body;
    const userId = req.session.user._id;

    // validate basic types
    const lat = latitude !== undefined ? Number(latitude) : undefined;
    const lon = longitude !== undefined ? Number(longitude) : undefined;
    const avg = avg_power !== undefined ? Number(avg_power) : undefined;

    const update = {};
    if (!Number.isNaN(lat)) update.latitude = lat;
    if (!Number.isNaN(lon)) update.longitude = lon;
    if (!Number.isNaN(avg)) update.avg_power = avg;

    if (Object.keys(update).length === 0) {
      return res.status(400).json({ status: "error", message: "No valid fields provided" });
    }

    const user = await User.findByIdAndUpdate(userId, update, { new: true }).lean();
    if (!user) return res.status(404).json({ status: "error", message: "User not found" });

    // update session copy
    req.session.user = user;

    return res.json({ status: "success", user });
  } catch (err) {
    console.error("Profile update error:", err);
    return res.status(500).json({ status: "error", message: "Server error" });
  }
});
