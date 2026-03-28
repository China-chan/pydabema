<p align="center">
 Abema Dash Encryption Decryptor
</p>

## Table of Contents
- [About](#about)
- [What This Is](#what-this-is)
- [Requirements](#requirements)
- [Usage](#usage)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Using as a Python Module](#2-using-as-a-python-module)
  - [3. Using the Manual Script](#3-using-the-manual-script)
- [FAQ](#faq)
  - **1. Work on Premium?**
  - **2. How to Get a KID?**
- [Issues](#issues)

---

## About
This project provides code to decrypt the encryption used by:  
https://license.p-c3-e.abema-tv.com/abematv-dash  

All processing is implemented purely in Python, without relying on Node.js or similar environments.

---

## What This Is
This repository is a continued / extended version of the original project:  
👉 https://github.com/NyaShinn1204/abema-dash-decryptor

---

## Requirements
- Python 3.12 or later  
- Japan VPN  
- See `requirements.txt` for Python dependencies  

---

## Usage

### 1. Clone the Repository

First, clone the repository:

```bash id="clone01"
git clone [https://github.com/NyaShinn1204/abema-dash-decryptor](https://github.com/China-chan/pydabema)
````

---

### 2. Using as a Python Module

After cloning, you can use `pydabema` as a module:

```python
import pydabema

response = pydabema.decrypt(
    content_type="program",          # Target content type
    content_id="19-171_s2_p38",      # Target content id
    kid="KTofq8TORPmxAFWIYyODfg"     # Target content kid
    session=None,                    # Optional session (e.g., use premium)
    member_id=None                   # Optional session info
)
```

> ⚠️ Note: Argument details may vary depending on the implementation.

---

### 3. Using the Manual Script

The `manual.py` script is included inside the cloned repository under `pydabema/`.

Run it with:

```bash id="manual01"
python -m pydabema.manual
```

or:

```bash id="manual02"
python pydabema/manual.py
```

Follow the on-screen instructions and enter the URL when prompted.

---


## FAQ

### 1. Is this work on premium content?

Yes, it works. However, you need a token that grants access to premium content to run it.

Here's how:
```python
import requests
import pydabema

session = requests.Session()
session.headers.update(
  {
    "authorization": "Bearer eyXXXXXX....."
  }
)
member_id = "CSKoXXXXXX....."

response = pydabema.decrypt(
    content_type="program",          # Target content type
    content_id="90-2046_s1_p801",    # Target content id
    kid="Fh1Id0HBSVeIyQ0_humWCw"     # Target content kid
    session=session,                 # Optional session (e.g., use premium)
    member_id=member_id              # Optional session info
)
```


### 2. How to Get a KID?

#### Step 1: Access the MPD file

Open the following URL in your browser:

``https://ds-vod-abematv.akamaized.net/program/{episode_id}/manifest.mpd``

Replace `{episode_id}` with the target episode ID.  
Example:

```
19-171_s2_p1
```

---

#### Step 2: Find the `default_KID`

Search in the MPD file for the following tag:

```
<ContentProtection schemeIdUri="urn:mpeg:dash:mp4protection:2011" value="cenc" cenc:default_KID="XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"/>
````
Copy the value of `cenc:default_KID`.

---

#### Step 3: Convert KID to Base64 (URL-safe)

The extracted KID must be converted into a Base64 (URL-safe) format.

Example in Python:

```python id="kidconv01"
import base64

kid = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"

kid_base64 = base64.b64encode(
    bytes.fromhex(kid.replace("-", ""))
).decode("utf-8").replace("==", "").replace("+", "-").replace("/", "_")

print(kid_base64)
````

#### Notes

* Remove all `-` (hyphens) before converting.
* The result is a **URL-safe Base64 string**.

---

## Issues

If you encounter any problems, please open an issue on the repository.
