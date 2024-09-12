import io
import streamlit as st
from pyomo.environ import Var
import pandas as pd


from llm_optimizer.models.llm import LinearOptimizationModel
from llm_optimizer.llm.communication_instructor import ask_llm_for_pyomo_model
from llm_optimizer.calculations.lin_optimization_logic import construct_pyomo_model, solve

st.title("Linear Optimization Assistant")

with st.form("Task"):
   task = st.text_area("Insert a problem formulation in natural language:")
   submit_button = st.form_submit_button("Solve")

if submit_button:
   if not task:
      st.write("no input given")
      
   else:
      structured_llm_response: LinearOptimizationModel = ask_llm_for_pyomo_model(
         task,
         validate_input=False,
         max_retries=1,
         mock=False
      )

      pyomo_model = construct_pyomo_model(structured_llm_response)
      solution = solve(pyomo_model)

      
      st.markdown("## Problem Formulation:")
      st.latex(structured_llm_response.mathematical_formulation)
      st.markdown("## Optimized Variables:")
      for model_var in solution.component_objects(Var, active=True):
         st.write(model_var.doc)
         pyomo_var = getattr(solution, str(model_var))
         for idx in pyomo_var:
            st.write(f"{model_var}[{idx}]: {pyomo_var[idx]()}")
      st.markdown("## Solution:")
      st.write(f"{structured_llm_response.objective.doc}: {solution.my_objective()}")
      st.markdown("## Pyomo Model:")
      with (outstream := io.StringIO()):
         solution.pprint(ostream=outstream)
         st.markdown(outstream.getvalue())
     

   