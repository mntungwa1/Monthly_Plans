"""Password gates; all secrets remain on the Streamlit server."""
import hashlib
import hmac
import time

import streamlit as st

def setting(name, default=''):
    try:return st.secrets.get(name, default)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):return default

def gate(scope, secret_name):
    """Return True only after this session passes the configured password gate."""
    expected=str(setting(secret_name))
    if not expected.strip():
        st.error(f'{secret_name} is missing or blank. Set it privately in Streamlit Secrets to enable access.')
        st.session_state.pop(scope+'_auth',None)
        return False
    token=hashlib.sha256(expected.encode()).hexdigest()
    now=time.time();state=st.session_state.get(scope+'_auth')
    if state and state['token']==token and now-state['last_seen']<1800:
        state['last_seen']=now;return True
    st.session_state.pop(scope+'_auth',None)
    if now < st.session_state.get(scope+'_locked_until',0):
        st.warning('Too many unsuccessful attempts. Wait one minute before trying again.')
        return False
    with st.form(scope+'_login'):
        entered=st.text_input('App password' if scope=='app' else 'Admin password',type='password',key=scope+'_password_input')
        submitted=st.form_submit_button('Sign in' if scope=='app' else 'Unlock admin dashboard')
    if submitted:
        st.session_state.pop(scope+'_password_input',None)
        if hmac.compare_digest(entered.encode(),expected.encode()):
            st.session_state[scope+'_auth']={'token':token,'last_seen':now}
            st.session_state[scope+'_failed']=0
            st.rerun()
        else:
            count=st.session_state.get(scope+'_failed',0)+1
            st.session_state[scope+'_failed']=count
            if count>=5:
                st.session_state[scope+'_locked_until']=now+60
                st.session_state[scope+'_failed']=0
            st.error('Password is incorrect.')
    return False
