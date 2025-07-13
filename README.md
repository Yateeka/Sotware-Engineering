# Software-Engineering
## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Yateeka/Sotware-Engineering.git
cd Sotware-Engineering
```

### 2. Navigate to the frontend folder and install dependencies

```bash
cd frontend
npm install
```

### 3. Run the Development Server

```bash
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🧼 Git Hygiene

To avoid committing unnecessary files like libraries or build folders, we use a `.gitignore` file that excludes:

- `node_modules/`
- `.next/`
- `build/`, `dist/`
- `.env`

If you accidentally committed these before adding them to `.gitignore`, run:

```bash
git rm -r --cached node_modules/ .next/ build/ dist/
git commit -m "Apply .gitignore and clean tracked files"
```

---
