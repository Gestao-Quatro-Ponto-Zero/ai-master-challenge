"""
DealSignal UI — Filter helpers.

Manages cascading filter state in st.session_state and computes
valid dropdown options for office → manager → sales_agent hierarchy.
"""

import pandas as pd
import streamlit as st

from config.constants import RATING_ORDER
from app.ui.data_loaders import ALL, FILTER_KEYS


def _init_filters() -> None:
    """Initialises filter keys in session_state if not already set."""
    for key in FILTER_KEYS:
        if key not in st.session_state:
            st.session_state[key] = ALL
    if "selected_deal_id" not in st.session_state:
        st.session_state["selected_deal_id"] = None


def _reset_filters() -> None:
    """Resets all filter dropdowns and the deal selection to their default values."""
    for key in FILTER_KEYS:
        st.session_state[key] = ALL
    if "sel_ratings" in st.session_state:
        st.session_state["sel_ratings"] = RATING_ORDER
    st.session_state["selected_deal_id"] = None


def _validate_and_apply_cascade(df: pd.DataFrame) -> dict:
    """
    Top-down cascade: office → manager → sales_agent.

    Each level filters only by its parents, never by its children.
    Invalid selections are reset in order so that child options
    always reflect the validated parent value.
    """
    # 1) Office — no parent filter, always show all offices
    office = st.session_state.get("sel_office", ALL)
    valid_offices = sorted(df["office"].dropna().unique().tolist())
    if office != ALL and office not in valid_offices:
        office = ALL
        st.session_state["sel_office"] = ALL

    # 2) Manager — filtered by selected office
    mask_mgr = pd.Series(True, index=df.index)
    if office != ALL:
        mask_mgr = df["office"] == office
    valid_managers = sorted(df.loc[mask_mgr, "manager"].dropna().unique().tolist())

    manager = st.session_state.get("sel_manager", ALL)
    if manager != ALL and manager not in valid_managers:
        manager = ALL
        st.session_state["sel_manager"] = ALL

    # 3) Sales agent — filtered by selected office + manager
    mask_agent = mask_mgr.copy()
    if manager != ALL:
        mask_agent = mask_agent & (df["manager"] == manager)
    valid_agents = sorted(df.loc[mask_agent, "sales_agent"].dropna().unique().tolist())

    agent = st.session_state.get("sel_agent", ALL)
    if agent != ALL and agent not in valid_agents:
        st.session_state["sel_agent"] = ALL

    return {
        "office": valid_offices,
        "manager": valid_managers,
        "sales_agent": valid_agents,
    }
