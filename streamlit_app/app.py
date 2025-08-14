import time
import os
from typing import Optional

import requests
import streamlit as st


def initialize_session_state() -> None:
	if "api_base_url" not in st.session_state:
		default_base = os.getenv("BACKEND_URL", "http://localhost:8080")
		st.session_state.api_base_url = default_base
	if "access_token" not in st.session_state:
		st.session_state.access_token = None
	if "logged_in_email" not in st.session_state:
		st.session_state.logged_in_email = None
	if "last_generation_id" not in st.session_state:
		st.session_state.last_generation_id = None
	if "last_audio_bytes" not in st.session_state:
		st.session_state.last_audio_bytes = None
	if "account_data" not in st.session_state:
		st.session_state.account_data = None
	if "predictions_data" not in st.session_state:
		st.session_state.predictions_data = None
	if "active_page" not in st.session_state:
		st.session_state.active_page = "Login"


def get_auth_headers() -> dict:
	if not st.session_state.access_token:
		return {}
	return {"Authorization": f"Bearer {st.session_state.access_token}"}


def ui_sidebar() -> None:
	st.sidebar.header("Settings")
	st.session_state.api_base_url = st.sidebar.text_input(
		"Backend URL",
		value=st.session_state.api_base_url,
		help="FastAPI server base URL (e.g., http://localhost:8080)",
	)
	if st.session_state.access_token:
		st.sidebar.success("Authenticated")
		if st.sidebar.button("Log out"):
			st.session_state.access_token = None
			st.session_state.logged_in_email = None
			st.session_state.last_generation_id = None
			st.session_state.last_audio_bytes = None

	st.sidebar.markdown("---")
	st.sidebar.subheader("Navigation")
	pages_labels = ["Register", "Login", "Account", "Credit", "Generate", "History"]
	default_index = pages_labels.index(st.session_state.active_page) if st.session_state.active_page in pages_labels else 1
	selected_label = st.sidebar.radio("Page", pages_labels, index=default_index, key="nav_selection")
	st.session_state.active_page = selected_label


def register_form() -> None:
	st.subheader("Register")
	with st.form("register_form", clear_on_submit=False):
		email = st.text_input("Email", key="register_email")
		password = st.text_input("Password", type="password", key="register_password")
		submitted = st.form_submit_button("Create account")
		if submitted:
			try:
				resp = requests.post(
					f"{st.session_state.api_base_url}/register",
					json={"email": email, "password": password},
					timeout=15,
				)
				if resp.ok:
					st.success("Registration successful. You can now log in.")
					st.json(resp.json())
				else:
					st.error(f"Registration failed: {resp.status_code} - {resp.text}")
			except Exception as exc:
				st.error(f"Error: {exc}")


def login_form() -> None:
	st.subheader("Login")
	with st.form("login_form", clear_on_submit=False):
		email = st.text_input("Email", key="login_email")
		password = st.text_input("Password", type="password", key="login_password")
		submitted = st.form_submit_button("Sign in")
		if submitted:
			try:
				# OAuth2PasswordRequestForm expects form fields: username, password
				resp = requests.post(
					f"{st.session_state.api_base_url}/login",
					data={"username": email, "password": password},
					headers={"Content-Type": "application/x-www-form-urlencoded"},
					timeout=15,
				)
				if resp.ok:
					data = resp.json()
					st.session_state.access_token = data.get("access_token")
					st.session_state.logged_in_email = email
					st.success("Login successful")
				else:
					st.error(f"Login failed: {resp.status_code} - {resp.text}")
			except Exception as exc:
				st.error(f"Error: {exc}")


def account_info() -> None:
    st.subheader("Account")
    if not st.session_state.access_token:
        st.info("Please log in to view account info.")
        return

    with st.form("reload_account"):
        reload_clicked = st.form_submit_button("Reload account")
    if reload_clicked or st.session_state.account_data is None:
        try:
            resp = requests.get(
                f"{st.session_state.api_base_url}/me",
                headers=get_auth_headers(),
                timeout=15,
            )
            if resp.ok:
                st.session_state.account_data = resp.json()
            else:
                st.error(f"Failed to fetch account info: {resp.status_code} - {resp.text}")
        except Exception as exc:
            st.error(f"Error: {exc}")

    data = st.session_state.account_data or {}

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("User ID", value=str(data.get("id", "")), disabled=True)
        st.text_input("Email", value=str(data.get("email", "")), disabled=True)
    with col2:
        balance = (data.get("balance") or {}).get("amount")
        st.number_input("Balance (tokens)", value=float(balance or 0), disabled=True)

    with st.expander("Recent transactions"):
        transactions = data.get("transactions") or []
        if not transactions:
            st.caption("No transactions.")
        else:
            for tx in transactions[:10]:
                st.write(f"{tx.get('timestamp', '')} | {tx.get('transaction_type', '')} | {tx.get('amount', 0)} | {tx.get('transaction_status', '')}")


def credit_funds() -> None:
	st.subheader("Credit funds")
	if not st.session_state.access_token:
		st.info("Please log in to credit funds.")
		return
	amount = st.number_input("Amount in RUB", min_value=0.0, step=50.0, value=100.0, format="%f")
	if st.button("Credit"):
		try:
			resp = requests.get(
				f"{st.session_state.api_base_url}/credit",
				params={"amount": amount},
				headers=get_auth_headers(),
				timeout=30,
			)
			if resp.ok:
				st.success("Credit transaction created and processed.")
				st.json(resp.json())
			else:
				st.error(f"Credit failed: {resp.status_code} - {resp.text}")
		except Exception as exc:
			st.error(f"Error: {exc}")


def poll_generation_status(generation_id: str, max_wait_seconds: int = 60, interval_seconds: float = 2.0) -> Optional[str]:
	"""Polls generation status until DONE/FAILED or timeout. Returns final status or None on timeout."""
	status_url = f"{st.session_state.api_base_url}/predictions/{generation_id}/status"
	start = time.time()
	with st.spinner("Waiting for audio generation to complete..."):
		while time.time() - start < max_wait_seconds:
			resp = requests.get(status_url, headers=get_auth_headers(), timeout=15)
			if not resp.ok:
				st.error(f"Status check failed: {resp.status_code} - {resp.text}")
				return None
			data = resp.json()
			status = data.get("status") or data.get("Status") or data.get("state")
			if status in {"DONE", "FAILED"}:
				return status
			time.sleep(interval_seconds)
	return None


def fetch_audio(generation_id: str) -> Optional[bytes]:
	url = f"{st.session_state.api_base_url}/predictions/{generation_id}/audio"
	resp = requests.get(url, headers=get_auth_headers(), timeout=60)
	if resp.ok and resp.headers.get("content-type", "").startswith("audio"):
		return resp.content
	return None


def generate_audio() -> None:
	st.subheader("Generate audio")
	if not st.session_state.access_token:
		st.info("Please log in to generate audio.")
		return
	text = st.text_area("Text to synthesize", height=160)
	col1, col2 = st.columns(2)
	with col1:
		generate_clicked = st.button("Generate")
	with col2:
		check_clicked = st.button("Check last status")

	if generate_clicked and text.strip():
		try:
			resp = requests.post(
				f"{st.session_state.api_base_url}/predict",
				params={"text": text},
				headers=get_auth_headers(),
				timeout=60,
			)
			if resp.ok:
				data = resp.json()
				generation_id = data.get("id") or data.get("generation_id") or data.get("uuid")
				st.session_state.last_generation_id = generation_id
				st.info(f"Generation created. ID: {generation_id}")

				final_status = poll_generation_status(generation_id)
				if final_status == "DONE":
					audio_bytes = fetch_audio(generation_id)
					if audio_bytes:
						st.session_state.last_audio_bytes = audio_bytes
						st.success("Audio ready")
						st.audio(audio_bytes, format="audio/wav")
					else:
						st.warning("Audio not available yet. Try 'Check last status'.")
				elif final_status == "FAILED":
					st.error("Generation failed.")
				else:
					st.warning("Timed out waiting for generation to complete. Use 'Check last status'.")
			else:
				st.error(f"Generation request failed: {resp.status_code} - {resp.text}")
		except Exception as exc:
			st.error(f"Error: {exc}")

	if check_clicked and st.session_state.last_generation_id:
		status = poll_generation_status(st.session_state.last_generation_id, max_wait_seconds=1, interval_seconds=0.5)
		if status == "DONE":
			audio_bytes = fetch_audio(st.session_state.last_generation_id)
			if audio_bytes:
				st.session_state.last_audio_bytes = audio_bytes
				st.success("Audio ready")
				st.audio(audio_bytes, format="audio/wav")
			else:
				st.info("Still processing...")
	elif check_clicked and not st.session_state.last_generation_id:
		st.info("No previous generation. Use 'Generate' first.")


def predictions_list() -> None:
    st.subheader("My generations")
    if not st.session_state.access_token:
        st.info("Please log in to view predictions.")
        return

    with st.form("reload_predictions"):
        reload_clicked = st.form_submit_button("Reload history")
    if reload_clicked or st.session_state.predictions_data is None:
        try:
            resp = requests.get(
                f"{st.session_state.api_base_url}/predictions",
                headers=get_auth_headers(),
                timeout=30,
            )
            if resp.ok:
                st.session_state.predictions_data = resp.json()
            else:
                st.error(f"Failed to fetch predictions: {resp.status_code} - {resp.text}")
        except Exception as exc:
            st.error(f"Error: {exc}")

    items = st.session_state.predictions_data or []
    if not items:
        st.caption("No history yet.")
        return

    for item in items:
        with st.container(border=True):
            st.write(f"ID: {item.get('id', '')}")
            st.write(f"Status: {item.get('status', '')}")
            st.write(f"Tokens: {item.get('tokens_spent', 0)}")
            st.write(f"Text: {item.get('text', '')}")
            st.write(f"Timestamp: {item.get('timestamp', '')}")
            gen_id = item.get('id')
            cols = st.columns(2)
            with cols[0]:
                if st.button("Check status", key=f"check_{gen_id}"):
                    status = poll_generation_status(str(gen_id), max_wait_seconds=1, interval_seconds=0.5)
                    if status == "DONE":
                        st.success("DONE")
                    elif status == "FAILED":
                        st.error("FAILED")
                    else:
                        st.info("Processing...")
            with cols[1]:
                if st.button("Play audio", key=f"play_{gen_id}"):
                    audio_bytes = fetch_audio(str(gen_id))
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/wav")
                    else:
                        st.warning("Audio not available.")


def main() -> None:
	st.set_page_config(page_title="KCSyth Educ - TTS", page_icon="🎙️", layout="centered")
	initialize_session_state()
	ui_sidebar()

	st.title("KCSyth Educ - TTS Console")

	if st.session_state.logged_in_email:
		st.caption(f"Logged in as {st.session_state.logged_in_email}")

	pages = {
		"Register": register_form,
		"Login": login_form,
		"Account": account_info,
		"Credit": credit_funds,
		"Generate": generate_audio,
		"History": predictions_list,
	}
	render_fn = pages.get(st.session_state.active_page, login_form)
	render_fn()


if __name__ == "__main__":
	main()


