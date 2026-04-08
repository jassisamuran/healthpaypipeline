"""
graph.py
--------
LangGraph StateGraph – wires up the 5 nodes in the required order.

Flow:
  START → segregator → id_agent → discharge_agent → bill_agent → aggregator → END

The Segregator classifies pages and writes routing info to state.
Each extraction agent reads ONLY its assigned page numbers – never the whole PDF.
"""

import sys, os

sys.path.insert(0, os.path.dirname(__file__))

from langgraph.graph import StateGraph, END

from models import ClaimState
from agents.segregator import segregator_node
from agents.id_agent import id_agent_node
from agents.discharge_agent import discharge_agent_node
from agents.bill_agent import bill_agent_node
from agents.aggregator import aggregator_node


def build_graph():
    builder = StateGraph(ClaimState)

    builder.add_node("segregator", segregator_node)
    builder.add_node("id_agent", id_agent_node)
    builder.add_node("discharge_agent", discharge_agent_node)
    builder.add_node("bill_agent", bill_agent_node)
    builder.add_node("aggregator", aggregator_node)

    builder.set_entry_point("segregator")
    builder.add_edge("segregator", "id_agent")
    builder.add_edge("id_agent", "discharge_agent")
    builder.add_edge("discharge_agent", "bill_agent")
    builder.add_edge("bill_agent", "aggregator")
    builder.add_edge("aggregator", END)

    return builder.compile()


claim_graph = build_graph()
