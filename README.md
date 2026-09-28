# ANMS ATTENDANCE — Authpur National Model Higher Secondary School

An enterprise-ready, modular Biometric Attendance Management System for Authpur National Model Higher Secondary School written in Python, featuring real-time OpenCV face detection, Local Binary Patterns Histograms (LBPH) facial recognition, SQLite relational storage with parameterized queries, a sleek CustomTkinter cybernetic dark UI, and futuristic holographic HUD overlays.

---

## 🏛 System Architecture & High-Level Design

The application follows strict Separation of Concerns (SoC) across five distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│                       Presentation Layer                    │
│            CustomTkinter GUI (Views & Visualizer HUD)       │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
┌──────────────▼──────────────┐ ┌─────────────▼───────────────┐
│     Vision & AI Layer       │ │       Database Layer        │
│   - Haar Cascade Detection  │ │  - SQLite Schema & WAL Mode │
│   - CLAHE Normalization     │ │  - Parameterized Queries    │
│   - LBPH 1:1 Verification   │ │  - Duplicate Prevention     │
│   - Holographic HUD Renderer│ │  - Transaction Safety       │
└──────────────┬──────────────┘ └─────────────┬───────────────┘
               │                              │
┌──────────────▼──────────────────────────────▼───────────────┐
│                    Hardware & Platform Layer                │
│    - VideoCapture Hardware & Adaptive Virtual Simulator     │
│    - File System Storage (Samples, Models, XML Cascades)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗄 Database Schema Design

The system utilizes SQLite with Foreign Keys and Write-Ahead Logging (WAL) enabled. Parameterized queries (`?` placeholders) are used exclusively across all database operations to eliminate SQL injection vulnerabilities.

### Tables & Constraints:

1. **`students`**
   - `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
   - `name`: `TEXT NOT NULL`
   - `class_name`: `TEXT NOT NULL`
   - `section`: `TEXT NOT NULL`
   - `roll_number`: `TEXT NOT NULL`
   - `created_at`: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
   - `CONSTRAINT uq_student UNIQUE (class_name, section, roll_number)`

2. **`teachers`**
   - `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
   - `name`: `TEXT NOT NULL`
   - `subject`: `TEXT NOT NULL`
   - `teacher_uid`: `TEXT NOT NULL UNIQUE`
   - `created_at`: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

3. **`face_samples`**
   - `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
   - `user_role`: `TEXT NOT NULL CHECK(user_role IN ('student', 'teacher'))`
   - `user_id`: `INTEGER NOT NULL`
   - `sample_path`: `TEXT NOT NULL`
   - `sample_index`: `INTEGER NOT NULL`
   - `created_at`: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

4. **`attendance`**
   - `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
   - `user_id`: `INTEGER NOT NULL`
   - `user_role`: `TEXT NOT NULL CHECK(user_role IN ('student', 'teacher'))`
   - `name`: `TEXT NOT NULL`
   - `date`: `TEXT NOT NULL` *(Format: YYYY-MM-DD)*
   - `time`: `TEXT NOT NULL` *(Format: HH:MM:SS)*
   - `status`: `TEXT NOT NULL DEFAULT 'Present'`
   - `confidence`: `REAL`
   - `created_at`: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
   - `CONSTRAINT uq_user_attendance_per_day UNIQUE (user_role, user_id, date)`  
     *Prevents duplicate attendance for the same user on the same calendar day.*

---

## 🧠 Face Recognition Approach & Rationale

### Algorithm: OpenCV Local Binary Patterns Histograms (LBPH)
We chose OpenCV's native `cv2.face.LBPHFaceRecognizer` combined with Contrast Limited Adaptive Histogram Equalization (CLAHE) for the following reasons:

1. **Monotonic Illumination Invariance:**
   Standard Euclidean pixel matching fails under shadow or varying classroom lighting. LBPH constructs local $3 \times 3$ binary micro-texture descriptors:
   $$\text{LBP}(x_c, y_c) = \sum_{p=0}^{P-1} s(i_p - i_c) 2^p, \quad s(x) = \begin{cases} 1 & x \ge 0 \\ 0 & x < 0 \end{cases}$$
   Because it evaluates whether neighbor pixels are brighter or darker than the center pixel, uniform changes in brightness preserve the texture code.

2. **Multi-Angle Enrollment:**
   Registration captures 25 distinct crops per user with active pose guidance (front, slight left, slight right, chin up, chin down). LBPH partitions the face into an $8 \times 8$ grid of cells and concatenates their local histograms, capturing spatial structure across head poses.

3. **1:1 Strict Biometric Verification:**
   Instead of searching an open database for arbitrary matches, our 2-Step verification requires valid credential entry first. The engine then verifies:
   - Does LBPH predict the user's enrolled label?
   - Is the dissimilarity distance $\le \text{LBPH\_CONFIDENCE\_THRESHOLD}$ (default: $68.0$)?
   - Are there $N$ consecutive matching frames (default: 4) to prevent transient false positives?

4. **Zero Heavyweight External Dependencies:**
   Does not require gigabytes of PyTorch or TensorFlow model weights. Runs at 30+ FPS on any standard CPU.

---

## 📁 Project Structure

```
facedetection attendance/
├── config.py                 # Central configuration (paths, thresholds, styling)
├── main.py                   # Application launch script
├── requirements.txt          # Python dependencies
├── README.md                 # System manual & technical documentation
│
├── database/
│   ├── __init__.py
│   ├── db_manager.py         # SQLite CRUD operations & parameterized queries
│   └── schema.sql            # Table definitions & integrity constraints
│
├── face_recognition/
│   ├── __init__.py
│   ├── detector.py           # Haar Cascade detection & CLAHE normalization
│   ├── recognizer.py         # LBPH training, model save/load & 1:1 verification
│   ├── visualizer.py         # Futuristic holographic HUD overlay rendering
│   └── cascades/             # Bundled OpenCV Haar XML classifiers
│       ├── haarcascade_frontalface_default.xml
│       └── haarcascade_frontalface_alt2.xml
│
├── ui/
│   ├── __init__.py
│   ├── app.py                # Main CTk application window & navigation router
│   ├── components.py         # Reusable widgets (cards, video canvas, headers)
│   ├── main_menu.py          # Dashboard with role selection & live stats
│   ├── role_menu.py          # Student & Teacher sub-portal selector
│   ├── registration_view.py  # Credential enrollment & live multi-angle capture
│   ├── attendance_view.py    # Credential validation & holographic face verification
│   └── records_view.py       # Attendance audit log table & CSV exporter
│
├── utils/
│   ├── __init__.py
│   ├── camera.py             # OpenCV VideoCapture wrapper with virtual fallback
│   ├── logger.py             # Standardized terminal & file logging
│   └── validators.py         # Input sanitization and format validators
│
└── data/                     # Auto-created storage
    ├── school_attendance.db  # SQLite database file
    ├── faces/                # User sample face crops (role_id/sample_XX.jpg)
    └── models/               # Serialized lbph_face_model.xml & label_map.json
```

---

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.8 to 3.14
- Operating System: macOS, Windows 10/11, or Linux (Ubuntu 20.04+)
- Functional webcam (optional — system includes an automated virtual webcam simulator if hardware is not connected)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

*Or manually install:*
```bash
pip install opencv-contrib-python customtkinter pillow numpy
```

---

## ▶ How to Run the Application

Execute `main.py` directly from the project directory:

```bash
python3 main.py
```

---

## 📖 Step-by-Step User Walkthrough

### 👨‍🎓 1. Student Registration
1. On the Main Menu, click **"Enter Student Portal"**.
2. Select **"Register / Login"**.
3. Fill in the required fields:
   - **Full Name**: e.g., `Rahul Sharma`
   - **Class / Grade**: e.g., `10`
   - **Section**: e.g., `A`
   - **Roll Number**: e.g., `23` *(Must be unique within Class & Section)*
4. Click **"Start Biometric Capture"**.
5. The webcam feed activates. Follow the on-screen prompts:
   - *Look straight into camera*
   - *Turn head slightly left*
   - *Turn head slightly right*
   - *Tilt chin slightly up*
   - *Tilt chin down / smile naturally*
6. Once 25 samples are gathered, the system saves the crops, registers the student in SQLite, and automatically trains the LBPH model.

---

### 👨‍🏫 2. Teacher Registration
1. On the Main Menu, click **"Enter Teacher Portal"**.
2. Select **"Register / Login"**.
3. Fill in the teacher fields:
   - **Full Name**: e.g., `Dr. Ananya Sen`
   - **Main Subject**: e.g., `Mathematics`
   - **Teacher UID**: e.g., `TCH-1042` *(Must be unique)*
4. Click **"Start Biometric Capture"**.
5. The camera records 25 biometric samples, updates the database, and retrains the model.

---

### 📸 3. Instant Face Attendance (Zero-Form Automated Marking)

No repetitive manual form-filling is required! Once registered, users mark attendance simply by standing in front of the camera.

1. Click **"Instant Face Attendance"** from the main dashboard or **"Sign In / Mark Attendance"** from the role portal.
2. The webcam stream immediately opens with live 1:N facial identification.
3. As soon as a registered face is detected:
   - A **floating holographic HUD hover details card** tracks the face in real-time with an angled leader line:
     ```
     ┌──────────────────────────────────────────────┐
     │ [✓] ATTENDANCE MARKED                        │
     │ Name : Rahul Sharma                          │
     │ Roll : 23                                    │
     │ Class: 10                                    │
     │ Sec  : A                                     │
     └──────────────────────────────────────────────┘
     ```
     *(For teachers, displays Name, UID, and Subject)*
   - **Automatic Logging**: Attendance is instantly recorded in the SQLite database without having to click any buttons or fill any forms.
   - **Duplicate Prevention**: If the person has already checked in earlier today, their hover badge displays `[ℹ] ALREADY RECORDED FOR TODAY`.
   - **Live Activity Feed**: The sidebar updates immediately showing the verified attendee, timestamp, and status.
   - **Continuous Operation**: The camera remains active so consecutive students or faculty can step up one by one and check in automatically.

---

### 📋 4. Attendance Records & CSV Export
1. On the Main Menu, click **"View Attendance Records"**.
2. Filter logs by role (*All*, *Students*, or *Teachers*) or search by student name.
3. Click **"Export CSV Report"** to generate a downloadable spreadsheet timestamped in the `data/` folder.

---

## 🛠 Common Errors & Fixes

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| `cv2.face has no attribute LBPHFaceRecognizer_create` | Standard `opencv-python` installed instead of `opencv-contrib-python`. | Run: `pip uninstall opencv-python && pip install opencv-contrib-python` |
| `OpenCV: AVFoundation didn't find any attached Video Input Devices` | No hardware webcam plugged in or camera permission denied. | The system automatically engages the built-in **Virtual Webcam Simulator**. To use a real camera, grant camera permissions in OS System Settings. |
| `Wrong input credentials. Please retry.` | Typo in Name, Class, Section, or Roll Number. | Verify exact Roll Number and spelling. The credential check is case-insensitive for names but requires exact Roll No / UID. |
| `Face not recognized. Please try again.` | Poor lighting, user sitting too far, or face tilted beyond threshold. | Face the camera directly in good lighting. If necessary, re-register with fresh samples. The threshold can also be adjusted in `config.py` (`LBPH_CONFIDENCE_THRESHOLD = 75.0`). |
| `Student already registered` | (Class, Section, Roll No) duplicate. | Each student must have a distinct roll number within their class and section. |

---

## 🔮 Future Improvements & Scaling

1. **Anti-Spoofing / Liveness Detection:** Integrate blink detection using eye aspect ratios (EAR) or color texture analysis to prevent photo/screen attacks.
2. **Deep Learning Embedding Backends:** Optional toggle in `config.py` for OpenCV DNN `cv2.FaceRecognizerSF` (SFace) or MobileFaceNet.
3. **SMS / Email Guardian Notifications:** Automated alerts sent to parents when student attendance is logged.
4. **Cloud / PostgreSQL Sync:** Multi-terminal synchronization across school campus gates using PostgreSQL.
