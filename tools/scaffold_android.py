# tools/scaffold_android.py
"""
Idempotent Android project scaffolder.

Usage:
  from tools import scaffold_android
  scaffold_android.scaffold()

This will create an 'android-app/' Gradle/Kotlin skeleton using
package info from PROGRAM_FEATURES.json or config.json.
"""

from pathlib import Path
import json
import re
from tools import safe_writer, logger

log = logger.get_logger()
ROOT = Path(__file__).resolve().parent.parent

# Paths
ANDROID_ROOT = ROOT / "android-app"
APP_MODULE = ANDROID_ROOT / "app"
SRC_MAIN = APP_MODULE / "src" / "main"
JAVA_DIR = SRC_MAIN / "java"
RES_DIR = SRC_MAIN / "res"
MANIFEST = SRC_MAIN / "AndroidManifest.xml"

# Templates
ROOT_BUILD_GRADLE = """// Top-level build file where you can add configuration options common to all sub-projects/modules.

buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath "com.android.tools.build:gradle:8.1.1"
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}
"""

SETTINGS_GRADLE = "include ':app'\nrootProject.name = 'android-app'\n"

APP_BUILD_GRADLE_KOTLIN = """plugins {
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
}

android {
    compileSdk 34

    defaultConfig {
        applicationId "{application_id}"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }

    namespace "{application_id}"
}

dependencies {
    implementation "org.jetbrains.kotlin:kotlin-stdlib:1.9.0"
    implementation "androidx.core:core-ktx:1.10.1"
    implementation "androidx.appcompat:appcompat:1.6.1"
    implementation "com.google.android.material:material:1.9.0"
}
"""

MANIFEST_XML = """<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{application_id}">

    <application
        android:allowBackup="true"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:icon="@mipmap/ic_launcher"
        android:supportsRtl="true"
        android:theme="@style/Theme.App">
        <activity android:name=".{main_activity}">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>

</manifest>
"""

MAIN_ACTIVITY_KOTLIN = """package {package};

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

class {activity_class} : AppCompatActivity() {{
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
    }}
}}
"""

ACTIVITY_MAIN_XML = """<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    tools:context=".{package}.{activity_class}">

    <TextView
        android:id="@+id/label"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="@string/hello_world"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        android:layout_marginTop="32dp"
        android:layout_marginStart="16dp"/>
</androidx.constraintlayout.widget.ConstraintLayout>
"""

STRINGS_XML = """<resources>
    <string name="app_name">{app_name}</string>
    <string name="hello_world">Hello World</string>
</resources>
"""

PROGUARD = """# Add your proguard rules here if needed.
"""

GITKEEP = ""  # empty content for .gitkeep

# ----- helpers -----
def safe_write(path: Path, content: str, mode="merge"):
    safe_writer.write_file_safe(str(path), content, mode=mode)

def _sanitize_package(pkg: str) -> str:
    # simple validation: only letters, digits, underscore, dots
    if not pkg or not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$', pkg):
        raise ValueError(f"Invalid package name: {pkg}")
    return pkg

def _package_to_path(pkg: str) -> Path:
    return Path(pkg.replace('.', '/'))

def _load_package_from_features():
    pf = ROOT / "PROGRAM_FEATURES.json"
    if not pf.exists():
        return None
    try:
        data = json.loads(pf.read_text(encoding="utf-8"))
    except Exception:
        return None
    # try nested keys: android.package or androidPackage or package
    android = data.get("android") if isinstance(data.get("android"), dict) else {}
    pkg = android.get("package") or data.get("androidPackage") or data.get("package")
    app_name = data.get("name") or data.get("appName") or "MyApp"
    return pkg, app_name

def _load_package_from_config():
    cfg = ROOT / "config.json"
    if not cfg.exists():
        return None
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data.get("android_package") or data.get("androidPackage") or data.get("package"), data.get("project", "MyApp")

# ----- main scaffold -----
def scaffold():
    log.info("Scaffolding Android project...")

    # Determine package and app name
    pkg_app = _load_package_from_features() or _load_package_from_config()
    if pkg_app and pkg_app[0]:
        try:
            package_name = _sanitize_package(pkg_app[0])
        except ValueError:
            log.warn(f"Invalid package name in inputs: {pkg_app[0]}; falling back to com.example.app")
            package_name = "com.example.app"
        app_name = pkg_app[1] if pkg_app[1] else "MyApp"
    else:
        package_name = "com.example.app"
        app_name = "MyApp"

    log.info(f"Using package: {package_name}, app name: {app_name}")

    # Create directories
    ANDROID_ROOT.mkdir(parents=True, exist_ok=True)
    APP_MODULE.mkdir(parents=True, exist_ok=True)
    (APP_MODULE / "src").mkdir(parents=True, exist_ok=True)
    SRC_MAIN.mkdir(parents=True, exist_ok=True)
    RES_DIR.mkdir(parents=True, exist_ok=True)

    # write root build files
    safe_write(ANDROID_ROOT / "build.gradle", ROOT_BUILD_GRADLE, mode="merge")
    safe_write(ANDROID_ROOT / "settings.gradle", SETTINGS_GRADLE, mode="merge")

    # app build.gradle
    safe_write(APP_MODULE / "build.gradle", APP_BUILD_GRADLE_KOTLIN.format(application_id=package_name), mode="merge")
    safe_write(APP_MODULE / "proguard-rules.pro", PROGUARD, mode="merge")

    # AndroidManifest
    main_activity_class = "MainActivity"
    manifest_text = MANIFEST_XML.format(application_id=package_name, main_activity=main_activity_class)
    safe_write(MANIFEST, manifest_text, mode="merge")

    # create package path for Kotlin/Java
    pkg_path = JAVA_DIR / _package_to_path(package_name)
    pkg_path.mkdir(parents=True, exist_ok=True)

    # MainActivity.kt
    activity_path = pkg_path / f"{main_activity_class}.kt"
    activity_text = MAIN_ACTIVITY_KOTLIN.format(package=package_name, activity_class=main_activity_class)
    safe_write(activity_path, activity_text, mode="merge")

    # layout and resources
    layout_dir = RES_DIR / "layout"
    layout_dir.mkdir(parents=True, exist_ok=True)
    safe_write(layout_dir / "activity_main.xml", ACTIVITY_MAIN_XML.format(package=package_name, activity_class=main_activity_class), mode="merge")

    mipmap_dir = RES_DIR / "mipmap"
    mipmap_dir.mkdir(parents=True, exist_ok=True)
    # create placeholders so gradle won't complain
    safe_write(mipmap_dir / ".gitkeep", GITKEEP, mode="merge")

    values_dir = RES_DIR / "values"
    values_dir.mkdir(parents=True, exist_ok=True)
    safe_write(values_dir / "strings.xml", STRINGS_XML.format(app_name=app_name), mode="merge")

    # create .gitkeep at module root if needed
    safe_write(ANDROID_ROOT / ".gitkeep", GITKEEP, mode="merge")
    safe_write(APP_MODULE / ".gitkeep", GITKEEP, mode="merge")

    # update memory/todo.json — add entry indicating scaffold done (if not present)
    todo_path = ROOT / "memory" / "todo.json"
    try:
        todo = json.loads(todo_path.read_text(encoding="utf-8")) if todo_path.exists() else {"tasks": []}
    except Exception:
        todo = {"tasks": []}
    # add a scaffolding status task (idempotent)
    ids = {t.get("id") for t in todo.get("tasks", []) if t.get("id")}
    scaffold_task = {"id": "scaffold:android", "title": "Scaffold Android project", "status": "done", "source": "scaffolder"}
    if scaffold_task["id"] not in ids:
        todo["tasks"].append(scaffold_task)
        safe_writer.write_file_safe(str(todo_path), json.dumps(todo, indent=2), mode="merge")
        log.info("Added scaffold completion to memory/todo.json")

    log.success(f"Android scaffold created at {ANDROID_ROOT}")
