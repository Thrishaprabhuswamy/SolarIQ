// ============================
// 🌞 SOLARIQ Node Backend (Frontend Server)
// ============================
const express = require("express");
const mongoose = require("mongoose");
const bcrypt = require("bcryptjs");
const session = require("express-session");
const bodyParser = require("body-parser");
const axios = require("axios"); // ✅ For calling Flask API
const User = require("./models/user");

const app = express();

// ============================
// ⚙️ MongoDB Connection
// ============================
mongoose.connect("mongodb://127.0.0.1:27017/solarMonitor");

mongoose.connection.on("connected", () => {
  console.log("✅ MongoDB connected successfully");
});

mongoose.connection.on("error", (err) => {
  console.error("❌ MongoDB connection error:", err);
});

mongoose.connection.on("disconnected", () => {
  console.warn("⚠️ MongoDB disconnected");
});


// ============================
// 🧩 Middleware
// ============================
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static("public"));
app.set("view engine", "ejs");

app.use(
  session({
    secret: "solar_secret_key",
    resave: false,
    saveUninitialized: false,
  })
);

// ✅ Auth guard middleware
function isAuthenticated(req, res, next) {
  if (!req.session.user) {
    console.log("⚠️ Unauthorized access attempt — redirecting to login");
    return res.redirect("/login");
  }
  next();
}

// ============================
// 🏠 Routes
// ============================

// Root → redirect to login
app.get("/", (req, res) => res.redirect("/login"));

// Login page
app.get("/login", (req, res) => res.render("login"));

// Signup page
app.get("/signup", (req, res) => res.render("signup"));

// ============================
// 📝 Signup Route
// ============================
app.post("/signup", async (req, res) => {
  try {
    const { username, email, password, confirmPassword, latitude, longitude, avg_power } = req.body;

    // Basic validation
    if (!username || !email || !password || !confirmPassword || !latitude || !longitude || !avg_power)
      return res.send("⚠️ Please fill all fields!");

    if (password !== confirmPassword)
      return res.send("⚠️ Passwords do not match!");

    const existingUser = await User.findOne({ $or: [{ username }, { email }] });
    if (existingUser)
      return res.send("⚠️ Username or Email already exists!");

    const hashedPassword = await bcrypt.hash(password, 10);
    const newUser = new User({
      username,
      email,
      password: hashedPassword,
      latitude,
      longitude,
      avg_power,
    });

    await newUser.save();
    console.log(`✅ User registered: ${username}`);
    res.redirect("/login");
  } catch (error) {
    console.error("❌ Signup error:", error);
    res.status(500).send("Internal Server Error");
  }
});

// ============================
// 🔐 Login Route
// ============================
app.post("/login", async (req, res) => {
  try {
    const { username, password } = req.body;
    const user = await User.findOne({ username });

    if (!user) return res.send("⚠️ No account found!");

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return res.send("⚠️ Incorrect password!");

    req.session.user = user;
    console.log(`🔐 ${username} logged in successfully`);
    res.redirect("/dashboard");
  } catch (error) {
    console.error("❌ Login error:", error);
    res.status(500).send("Internal Server Error");
  }
});

// ============================
// 📊 Dashboard Route (Protected)
// ============================
app.get("/dashboard", isAuthenticated, async (req, res) => {
  try {
    // ✅ Fetch solar data from Flask backend
    const flaskResponse = await axios.get("http://127.0.0.1:5000/history");

    const solarData = flaskResponse.data;

    // Render dashboard with both user info + solar data
    res.render("dashboard", { user: req.session.user, solarData });
  } catch (error) {
    console.error("⚠️ Could not connect to Flask backend:", error.message);
    res.render("dashboard", { user: req.session.user, solarData: null });
  }
});

// ============================
// 👩‍💼 Admin Route (View All Users)
// ============================
app.get("/users", async (req, res) => {
  try {
    const users = await User.find({}, "-password"); // exclude password field
    res.render("users", { users });
  } catch (error) {
    console.error("❌ Error fetching users:", error);
    res.status(500).send("Error retrieving user list");
  }
});

// ============================
// 🚪 Logout Route
// ============================
app.get("/logout", (req, res) => {
  req.session.destroy(() => res.redirect("/login"));
});

// ============================
// 🚀 Start Node Server
// ============================
const PORT = 3000;
app.listen(PORT, () => console.log(`🚀 Node frontend running at http://localhost:${PORT}`));
