# BioLab System

BioLab System is a professional Python-based desktop application designed for efficient management of chemical and biological inventories in laboratory environments. It features a secure login system, module-based navigation, and a modern user interface.

## Features

- **Secure Authentication**: User registration and login system with password protection.
- **Module Selection**: dedicated modules for Chemical and Biological inventories.
- **Inventory Management**:
    - Add new items to the inventory.
    - View existing inventory lists.
    - Update and delete items.
- **Modern UI**: Built with `ttkbootstrap` for a clean, professional, and responsive user interface.
- **Database Integration**: Uses SQLite for reliable local data storage.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd biolab_systems
    ```

2.  **Create a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the application:**
    ```bash
    python main.py
    ```

2.  **Login/Register:**
    - If you are a new user, click "Register" to create an account.
    - Login with your credentials.

3.  **Select Module:**
    - Choose between "Chemical Inventory" and "Biological Inventory" from the main hub.

4.  **Manage Inventory:**
    - Use the dashboard to manage your lab items.

## Technologies

- **Python 3.x**
- **ttkbootstrap**: For modern GUI components.
- **SQLite**: For database management.
- **ReportLab**: For generating reports (implied by requirements).

## Project Structure

- `main.py`: Entry point of the application.
- `app/`: Contains the application source code.
    - `auth.py`: Authentication logic.
    - `database.py`: Database connection and operations.
    - `ui.py`: Base UI components.
    - `ui_chemical.py`: Chemical inventory UI.
    - `ui_biological.py`: Biological inventory UI.
