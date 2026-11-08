from unittest.mock import patch
import pytest
from app.graders.council import SplitDecision, rating

def test_agreement_and_peer_exchange():
    with patch('app.graders.council.decision',side_effect=[{'score':3,'reason':'a'},{'score':4,'reason':'b'},{'score':4,'reason':'c'},{'score':4,'reason':'d'}]) as judge:
        result=rating('q','a')
        assert result['score']==7.5 and len(result['transcript'])==2
        assert judge.call_args_list[2].args[3]['reason']=='b'

def test_disagreement_never_published():
    with patch('app.graders.council.decision',side_effect=[{'score':n,'reason':'x'} for n in (2,4,2,4)]):
        with pytest.raises(SplitDecision,match='disagree') as split:
            rating('q','a')
        evidence = split.value.evidence()
        assert evidence["mean"] == 5
        assert [review["score"] for review in evidence["reviews"]] == [2.5, 7.5]
        assert len(evidence["transcript"]) == 2
