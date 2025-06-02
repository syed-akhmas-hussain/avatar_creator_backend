// Combined Express Server for Upload and Image Listing
const express = require("express");
const cors = require("cors");
const multer = require("multer");
const path = require("path");
const fs = require("fs");

const app = express();
app.use(cors());

// Root test route
app.get("/", (req, res) => {
  res.send("Hello, server is running!");
});

// ========== File Upload Section ==========
const userUploadsDir = path.join(__dirname, "useruploads");
if (!fs.existsSync(userUploadsDir)) {
  fs.mkdirSync(userUploadsDir);
}

const userStorage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, userUploadsDir);
  },
  filename: function (req, file, cb) {
    const uniqueName = `${Date.now()}-${file.originalname}`;
    cb(null, uniqueName);
  },
});

const userUpload = multer({ storage: userStorage });

app.post("/useruploads", userUpload.array("files", 10), (req, res) => {
  console.log("Files received:", req.files);

  if (!req.files || req.files.length === 0) {
    return res.status(400).json({ error: "No files uploaded" });
  }

  const filesInfo = req.files.map((file) => ({
    fieldname: file.fieldname,
    originalname: file.originalname,
    encoding: file.encoding,
    mimetype: file.mimetype,
    destination: file.destination,
    filename: file.filename,
    path: file.path,
    size: file.size,
    url: `http://localhost:5000/useruploads/${file.filename}`,
  }));

  res.json({ status: "success", uploaded: req.files.length, files: filesInfo });
});

// Serve uploaded files statically
app.use("/useruploads", express.static(userUploadsDir));

// ========== Image Listing Section ==========
const uploadsBaseDir = path.join(__dirname, "uploads");
app.use("/uploads", express.static(uploadsBaseDir));

const getCategorizedImages = (baseDir, baseUrl) => {
  const categories = {};
  const folders = fs.readdirSync(baseDir);

  folders.forEach((folder) => {
    const folderPath = path.join(baseDir, folder);
    const stat = fs.statSync(folderPath);

    if (stat.isDirectory()) {
      const files = fs.readdirSync(folderPath);
      categories[folder] = files.map((file) => ({
        filename: file,
        url: `${baseUrl}/${folder}/${file}`,
      }));
    }
  });

  return categories;
};

app.get("/images", (req, res) => {
  const baseUrl = "http://localhost:5000/uploads";

  try {
    const result = getCategorizedImages(uploadsBaseDir, baseUrl);
    res.json(result);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Error reading images" });
  }
});

// Start server
const PORT = 5000;
app.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`);
});
