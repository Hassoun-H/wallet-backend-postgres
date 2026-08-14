# Wallet Project

A complete backend system for managing financial accounts, transactions, and deposits.

## System Features Built So Far:
* Established initial database structures and tables.
* Implemented secure registration with constraints to prevent duplicate numbers or IDs.

## Current & Future Roadmap:
* Building the advanced financial deposit logic (`deposit`).
* Creating security protocols and transaction verification systems.
* **Future plan:** Implementation of a dedicated employees manager table with Admin controls.
> ⚠️ **Future Note:** The visibility function is not useful for the wallet structure in the future; it will be strictly used for search purposes only.

## 🛠 Tech Stack
* **Language:** Python
* **Interface:** NiceGUI (Web Dashboard)
* **Database:** PostgreSQL

## 🔌 API Endpoints Overview
* `POST /register` - Secure user registration.
* `POST /deposit` - Process financial deposits.
* `POST /transfer` - Handle secure balance transfers.

## 🚀 Getting Started
1. **Clone** the repository.
2. **Install** dependencies: `pip install -r requirements.txt`
3. **Run** the application: `python main.py`
