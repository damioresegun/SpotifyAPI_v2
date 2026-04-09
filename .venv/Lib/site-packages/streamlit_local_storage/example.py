import time 
import streamlit as st
from __init__ import _st_local_storage
from typing import Literal, Optional, Union, Any, Dict
# from streamlit_local_storage import LocalStorage

st.set_page_config(layout="wide")

class LocalStorage:
    """
    Component to help manager local storage for streamlit apps
    """
    # storedItems: Dict[str, Any]

    def __init__(self, key:str="storage_init"):

        """
        Initialise component

        Args:
            key: unique identified of component when mounted. 
            pause: time to pause after mounting component. Needed sometimes to allow all data to be loaded from browser.
        """

        self.storedKey = key
        if key not in st.session_state:
            self.storedItems:Dict[str, Any] = _st_local_storage(method="getAll", key=key, default={}) 
        #     while st.session_state[key] is None:
        #         time.sleep(0.1) 
        # else:
        #     self.storedItems:Dict[str, Any] = st.session_state[key]

        #     st.session_state[key] = self.storedItems

LocalStorageInit = LocalStorage() 

# localStorage = LocalStorage(key="testing") 
# localStorage.setItem("Jade", "Kyle", key="hi storage")
# result2 = localStorage.getItem("Jade") 
# # st.write(result2) 
# st.write(st.session_state['testing'])
