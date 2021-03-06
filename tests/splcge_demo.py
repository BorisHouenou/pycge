# Pyomo port of splcge.gms from GAMS Model Library


# ------------------------------------------- #
# Import packages
from pyomo.environ import *
import pandas as pd
import numpy as np
import time
import os


# ------------------------------------------- #
# MODEL OBJECT: "Container for problem"
# Create abstract model
model = AbstractModel()


# ------------------------------------------- #
# DEFINE SETS
model.i = Set(doc='goods')
model.h = Set(doc='factor')
model.u = Set(doc='SAM entry')


# ------------------------------------------- #
# Unnecessary: in GAMS, aliases
# model.j = SetOf(model.i)
# model.k = SetOf(model.h)
# model.v = SetOf(model.u)


# ------------------------------------------- #
# DEFINE PARAMETERS
model.sam = Param(model.u, model.u, doc='social accounting matrix')


def X0_init(model, i):
    return model.sam[i, 'HOH']


model.X0 = Param(model.i, initialize=X0_init,
                 doc='household consumption of the i-th good')


def F0_init(model, h, i):
    return model.sam[h, i]


model.F0 = Param(model.h, model.i, initialize=F0_init,
                 doc='the h-th factor input by the j-th firm')


def Z0_init(model, i):
    return sum(model.F0[h, i] for h in model.h)


model.Z0 = Param(model.i, initialize=Z0_init, doc='output of the j-th good')


def FF_init(model, h):
    return model.sam['HOH', h]


model.FF = Param(model.h, initialize=FF_init,
                 doc='factor endowment of the h-th factor')


# ------------------------------------------- #
# CALIBRATION


def alpha_init(model, i):
    return model.X0[i] / sum(model.X0[j] for j in model.i)

model.alpha = Param(model.i, initialize=alpha_init,
                    doc='share parameter in utility function')


def beta_init(model, h, i):
    return model.F0[h, i] / sum(model.F0[k, i] for k in model.h)

model.beta = Param(model.h, model.i, initialize=beta_init,
                   doc='share parameter in production function')


def b_init(model, i):
    return model.Z0[i] / np.prod([model.F0[h, i]**model.beta[h, i] for h in model.h])

model.b = Param(model.i, initialize=b_init,
                doc='scale paramater in production function')


# ------------------------------------------- #
# Define model system
# DEFINE VARIABLES

model.X = Var(model.i,
              initialize=X0_init,
              within=PositiveReals,
              doc='household consumption of the i-th good')

# def F_init(model, h, j):

model.F = Var(model.h, model.i,
              initialize=F0_init,
              within=PositiveReals,
              doc='the h-th factor input by the j-th firm')

model.Z = Var(model.i,
              initialize=Z0_init,
              within=PositiveReals,
              doc='output of the j-th good')


def p_init(model, v):
    return 1

model.px = Var(model.i,
               initialize=p_init,
               within=PositiveReals,
               doc='demand price of the i-th good')

model.pz = Var(model.i,
               initialize=p_init,
               within=PositiveReals,
               doc='supply price of the i-th good')

model.pf = Var(model.h,
               initialize=p_init,
               within=PositiveReals,
               #bounds = pf_fix,
               doc='the h-th factor price')


# Unnecessary: in gams, stores objective function *value*
# model.UU = Var(doc='utility [fictitious]')


# ------------------------------------------- #
# DEFINE EQUATIONS
# define constraints
def eqX_rule(model, i):
    return (model.X[i] == model.alpha[i] * sum(model.pf[h] * model.FF[h] / model.px[i] for h in model.h))

model.eqX = Constraint(model.i, rule=eqX_rule, doc='household demand function')


def eqpz_rule(model, i):
    return (model.Z[i] == model.b[i] * np.prod([model.F[h, i]**model.beta[h, i] for h in model.h]))

model.eqpz = Constraint(model.i, rule=eqpz_rule, doc='production function')


def eqF_rule(model, h, i):
    return (model.F[h, i] == model.beta[h, i] * model.pz[i] * model.Z[i] / model.pf[h])

model.eqF = Constraint(model.h, model.i, rule=eqF_rule,
                       doc='factor demand function')


def eqpx_rule(model, i):
    return (model.X[i] == model.Z[i])

model.eqpx = Constraint(model.i, rule=eqpx_rule,
                        doc='good market clearning condition')


def eqpf_rule(model, h):
    return (sum(model.F[h, j] for j in model.i) == model.FF[h])

model.eqpf = Constraint(model.h, rule=eqpf_rule,
                        doc='factor market clearning condition')


def eqZ_rule(model, i):
    return (model.px[i] == model.pz[i])

model.eqZ = Constraint(model.i, rule=eqZ_rule, doc='price equation')


# ------------------------------------------- #
# DEFINE OBJECTIVE
def obj_rule(model):
    return np.prod([model.X[i]**model.alpha[i] for i in model.i])

model.obj = Objective(rule=obj_rule, sense=maximize,
                      doc='utility function [fictitious]')


# ------------------------------------------- #
# CREATE MODEL INSTANCE

# Create directory   
moment=time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())
directory = (r'./results/')
if not os.path.exists(directory):
    os.makedirs(directory)
filename = directory + 'results_' 

data = DataPortal()
data.load(filename='../splcge_data_dir/set-i-.csv', format='set', set='i')
data.load(filename='../splcge_data_dir/set-h-.csv', format='set', set='h')
data.load(filename='../splcge_data_dir/set-u-.csv', format='set', set='u')
data.load(filename='../splcge_data_dir/param-sam-.csv', param='sam', format='array')

instance = model.create_instance(data)
instance.pf['LAB'].fixed = True
#instance.display()

# Create file for instance
with open(filename + "_instance_" + moment, 'w') as instance_output:
    instance_output.write("\nThis is the instance\n" )
    instance.display(ostream=instance_output)

# ------------------------------------------- #
# SOLVE
# Using NEOS external solver

# Select solver
solver = 'minos'  # 'ipopt', 'knitro', 'minos'
solver_io = 'nl'


# ------------------------------------------- #
# Display results
def pyomo_postprocess(options=None, instance=None, results=None):
    
    print("\n variables, objective, instance, and results object are all saved to files")
    





# ------------------------------------------- #
# To run as python script:

# This is an optional code path that allows the script to be run outside of
# pyomo command-line.  For example:  python splcge_demo.py

if __name__ == '__main__':
    #This replicates what the pyomo command-line tools does
    from pyomo.opt import SolverFactory
    from pyomo.opt import SolverResults
    import pyomo.environ
    import pickle
    #opt = SolverFactory(solver)
    #opt.options['max_iter'] = 20
    with SolverManagerFactory("neos") as solver_mgr:
        results = solver_mgr.solve(instance, opt=solver, tee=True)
        

    instance.solutions.store_to(results)
    
    pyomo_postprocess(instance=instance)
    
#-------------------------------------------------#
#OUTPUTS
    






# Create files for variables     
for v in instance.component_objects(Var, active=True):
    with open(filename + str(v) + "_" + moment + ".csv", 'w') as var_output:  
        varobject = getattr(instance, str(v))
        var_output.write ('{},{} \n'.format('Names', varobject ))
        for index in varobject:
            var_output.write ('{},{} \n'.format(index, varobject[index].value))

# Create file for objective
with open(filename + "_objective_" + moment + ".csv", 'w') as obj_output:
    obj_output.write ('{},{}\n'.format("objective", value(instance.obj)))
        

    
# Create file to save results as a pickle   
#Ask user what they would like to name their files (important to name export something specific for importing it back in)
export_pkl_filename = input("What would you like to name your pickle file?")
with open(filename + '_pickle_' + export_pkl_filename, 'wb') as pickle_output:
    pickle.dump(results, pickle_output)

#create file for results
with open(filename + "_results_" + moment, 'w') as results_output:
    results_output.write("\nThis is the results\n" )
    results.write(ostream=results_output)
print("Finished")


