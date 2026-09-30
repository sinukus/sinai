import pytest
from aicourt.types import Model
from aicourt.backends import MockBackend
from aicourt.cost import CostController, Budget
from aicourt.court import Court

def model(i,f,p,q,caps=frozenset({"general"})):
    return Model(i,f,p,p,q,caps)

def test_cost_order_and_family_independence():
    c=CostController([model("a1","A",.1,.7),model("a2","A",.2,.9),model("b","B",.3,.8)])
    assert c.candidates()[0].id=="a1"
    chosen=c.independent(n=3)
    assert len({m.family for m in chosen})==len(chosen)

def test_budget():
    c=CostController([], Budget(max_usd=.10))
    assert c.can_spend(.05,.04)
    assert not c.can_spend(.05,.06)

@pytest.mark.asyncio
async def test_confident_cheap_answer_stops():
    b=MockBackend("ok",.95)
    c=CostController([model("a","A",.1,.7),model("b","B",.2,.8)])
    assert await Court(b,c).answer("q")=="ok"
    assert len(b.calls)==1

@pytest.mark.asyncio
async def test_uncertain_answer_escalates():
    b=MockBackend("ok",.2)
    ms=[model("a","A",.1,.7),model("b","B",.2,.8),model("c","C",.5,.95)]
    assert await Court(b,CostController(ms)).answer("q")=="ok"
    assert len(b.calls)==7

@pytest.mark.asyncio
async def test_missing_capability_is_explicit():
    with pytest.raises(ValueError):
        await Court(MockBackend(),CostController([model("a","A",.1,.7)])).answer("q","maps")
