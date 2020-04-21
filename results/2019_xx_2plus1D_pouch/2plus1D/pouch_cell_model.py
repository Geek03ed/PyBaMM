import pybamm
import numpy as np
import os
import sys
import matplotlib.pyplot as plt

# change working directory to the root of pybamm
os.chdir(pybamm.root_dir())

# increase recursion limit for large expression trees
sys.setrecursionlimit(10000)

# load model and geometry
pybamm.set_logging_level("INFO")
options = {"current collector": "potential pair", "dimensionality": 2}
model = pybamm.lithium_ion.DFN(options)
geometry = model.default_geometry

# load parameters and process model and geometry
param = model.default_parameter_values
param.update({"C-rate": 1})
param.process_model(model)
param.process_geometry(geometry)

# set mesh
var = pybamm.standard_spatial_vars
submesh_types = model.default_submesh_types
var_pts = {
    var.x_n: 5,
    var.x_s: 5,
    var.x_p: 5,
    var.r_n: 10,
    var.r_p: 10,
    var.y: 15,
    var.z: 10,
}
mesh = pybamm.Mesh(geometry, submesh_types, var_pts)

# discretise model
disc = pybamm.Discretisation(mesh, model.default_spatial_methods)
disc.process_model(model, check_model=False)

# discharge timescale
tau = param.evaluate(pybamm.standard_parameters_lithium_ion.tau_discharge)

# solve model
t_end = 3600 / tau
t_eval = np.linspace(0, t_end, 120)
solver = pybamm.CasadiSolver(atol=1e-6, rtol=1e-6, root_tol=1e-3, mode="fast")
solution = solver.solve(model, t_eval)

# TO DO: 2+1D automated plotting
phi_s_cn = pybamm.ProcessedVariable(
    model.variables["Negative current collector potential [V]"],
    solution.t,
    solution.y,
    mesh=mesh,
)
phi_s_cp = pybamm.ProcessedVariable(
    model.variables["Positive current collector potential [V]"],
    solution.t,
    solution.y,
    mesh=mesh,
)
I = pybamm.ProcessedVariable(
    model.variables["Current collector current density [A.m-2]"],
    solution.t,
    solution.y,
    mesh=mesh,
)
T = pybamm.ProcessedVariable(
    model.variables["X-averaged cell temperature [K]"],
    solution.t,
    solution.y,
    mesh=mesh,
)
l_y = phi_s_cp.y_sol[-1]
l_z = phi_s_cp.z_sol[-1]
y_plot = np.linspace(0, l_y, 21)
z_plot = np.linspace(0, l_z, 21)

y_pos_tab = param.evaluate(pybamm.standard_parameters_lithium_ion.centre_y_tab_p)
z_pos_tab = param.evaluate(pybamm.standard_parameters_lithium_ion.centre_z_tab_p)
width_pos_tab = param.evaluate(pybamm.standard_parameters_lithium_ion.l_tab_p)
tab_start = y_pos_tab - width_pos_tab / 2
tab_end = y_pos_tab + width_pos_tab / 2


def plot(t):
    fig, ax = plt.subplots(figsize=(15, 8))
    plt.tight_layout()
    plt.subplots_adjust(left=-0.1)

    # find t index
    ind = (np.abs(solution.t - t)).argmin()

    # negative current collector potential
    plt.subplot(221)
    phi_s_cn_plot = plt.pcolormesh(
        y_plot,
        z_plot,
        np.transpose(phi_s_cn(y=y_plot, z=z_plot, t=solution.t[ind])),
        shading="gouraud",
    )
    plt.axis([0, l_y, 0, l_z])
    plt.xlabel(r"$y$")
    plt.ylabel(r"$z$")
    plt.title(r"$\phi_{s,cn}$ [V]")
    plt.set_cmap("cividis")
    plt.colorbar(phi_s_cn_plot)

    # positive current collector potential
    plt.subplot(222)
    phi_s_cp_plot = plt.pcolormesh(
        y_plot,
        z_plot,
        np.transpose(phi_s_cp(y=y_plot, z=z_plot, t=solution.t[ind])),
        shading="gouraud",
    )
    from skfem.visuals.matplotlib import draw

    mymesh = mesh["current collector"][0].fem_mesh
    draw(mymesh)
    plt.plot(tab_start, z_pos_tab, "ro")
    plt.plot(tab_end, z_pos_tab, "ro")
    plt.axis([0, l_y, 0, l_z])
    plt.xlabel(r"$y$")
    plt.ylabel(r"$z$")
    plt.title(r"$\phi_{s,cp}$ [V]")
    plt.set_cmap("viridis")
    plt.colorbar(phi_s_cp_plot)

    # current
    plt.subplot(223)
    I_plot = plt.pcolormesh(
        y_plot,
        z_plot,
        np.transpose(I(y=y_plot, z=z_plot, t=solution.t[ind])),
        shading="gouraud",
    )

    plt.axis([0, l_y, 0, l_z])
    plt.xlabel(r"$y$")
    plt.ylabel(r"$z$")
    plt.title(r"$I$ [A.m-2]")
    plt.set_cmap("plasma")
    plt.colorbar(I_plot)

    plt.subplots_adjust(
        top=0.92, bottom=0.15, left=0.10, right=0.9, hspace=0.5, wspace=0.5
    )

    # temperature
    plt.subplot(224)
    T_plot = plt.pcolormesh(
        y_plot,
        z_plot,
        np.transpose(T(y=y_plot, z=z_plot, t=solution.t[ind])),
        shading="gouraud",
    )

    plt.axis([0, l_y, 0, l_z])
    plt.xlabel(r"$y$")
    plt.ylabel(r"$z$")
    plt.title(r"$T$ [K]")
    plt.set_cmap("inferno")
    plt.colorbar(T_plot)

    plt.subplots_adjust(
        top=0.92, bottom=0.15, left=0.10, right=0.9, hspace=0.5, wspace=0.5
    )


plot(800 / tau)
plt.show()
