from transition_audit.audit import classify_transition


def test_row_flags_without_contract_link_remain_possible():
    assert classify_transition(source_flag=True, target_flag=False, interval_link=False, hierarchy_verified=False) == "POSSIBLE"


def test_account_link_and_unverified_hierarchy_do_not_confirm_direction():
    assert classify_transition(source_flag=False, target_flag=True, interval_link=True, hierarchy_verified=False) == "POSSIBLE"


def test_direction_is_inferred_only_with_link_and_verified_hierarchy():
    assert classify_transition(source_flag=True, target_flag=False, interval_link=True, hierarchy_verified=True) == "INFERRED"


def test_no_flag_or_link_is_unclassified():
    assert classify_transition(source_flag=False, target_flag=False, interval_link=False, hierarchy_verified=False) == "UNCLASSIFIED"
