from kfp.dsl import component, Input, Output, Dataset, pipeline, Artifact
from kfp import compiler
from kfp.client import Client

import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)


@component(
    base_image="quay.io/biocontainers/biobb_amber:4.2.0--pyhdfd78af_0",
    packages_to_install=["biobb-io==4.2.0"],
)
def download_pdb(pdb_code: str, output_pdb_file: Output[Artifact]):
    """Download a PDB structure from RCSB PDB database."""
    from biobb_io.api.pdb import pdb
    import os
    import shutil

    # Let biobb create the files in the current directory
    temp_pdb_path = f"{pdb_code}.pdb"
    prop = {"pdb_code": pdb_code}

    # Run the PDB download
    pdb(output_pdb_path=temp_pdb_path, properties=prop)

    # Copy the PDB file to the KFP-provided output location
    shutil.copy(temp_pdb_path, output_pdb_file.path)

    print(f"Downloaded PDB structure for {pdb_code}")
    print(f"Files created: {os.listdir('.')}")
    print(f"Copied main PDB file to: {output_pdb_file.path}")


@component(base_image="quay.io/biocontainers/biobb_amber:4.2.0--pyhdfd78af_0")
def prepare_pdb(input_pdb_file: Input[Artifact], output_prepared_pdb: Output[Artifact]):
    """Prepare PDB file for AMBER using pdb4amber tool."""
    import shutil
    import os
    import subprocess

    # Check if pdb4amber is available
    print("Verifying pdb4amber installation:")
    subprocess.run(["which", "pdb4amber"], check=True)

    # Copy the input file from Minio to a local path
    local_input_path = "input.pdb"
    shutil.copy(input_pdb_file.path, local_input_path)
    print(f"Copied input file from {input_pdb_file.path} to {local_input_path}")

    # Use a local output path
    local_output_path = "output.pdb"

    # Run the preparation using biobb
    from biobb_amber.pdb4amber.pdb4amber_run import pdb4amber_run

    pdb4amber_run(input_pdb_path=local_input_path, output_pdb_path=local_output_path)
    print(f"Generated prepared PDB file at: {local_output_path}")

    # Copy the result to the KFP output location
    shutil.copy(local_output_path, output_prepared_pdb.path)
    print(f"Copied prepared PDB from {local_output_path} to {output_prepared_pdb.path}")


@component(
    base_image="quay.io/biocontainers/biobb_amber:4.2.0--pyhdfd78af_0",  # Using the same working image
    packages_to_install=[],
)
def create_topology(
    input_pdb: Input[Artifact],
    output_pdb: Output[Artifact],
    output_top: Output[Artifact],
    output_crd: Output[Artifact],
):
    """Build AMBER topology for the protein structure."""
    from biobb_amber.leap.leap_gen_top import leap_gen_top
    import shutil
    import subprocess
    import os

    # Copy input from object storage to local path
    local_input_pdb = "input.pdb"
    shutil.copy(input_pdb.path, local_input_pdb)
    print(f"Copied input PDB from {input_pdb.path} to {local_input_pdb}")

    # Define local output paths
    local_output_pdb = "output.pdb"
    local_output_top = "system.top"
    local_output_crd = "system.crd"

    # Set forcefield properties
    prop = {"forcefield": ["protein.ff14SB"]}

    # Run topology generation
    leap_gen_top(
        input_pdb_path=local_input_pdb,
        output_pdb_path=local_output_pdb,
        output_top_path=local_output_top,
        output_crd_path=local_output_crd,
        properties=prop,
    )

    # Copy results back to object storage
    shutil.copy(local_output_pdb, output_pdb.path)
    shutil.copy(local_output_top, output_top.path)
    shutil.copy(local_output_crd, output_crd.path)

    print(f"Created system topology files:")
    print(f"  PDB: {output_pdb.path}")
    print(f"  TOP: {output_top.path}")
    print(f"  CRD: {output_crd.path}")


# Energy minimization


@component(
    base_image="quay.io/biocontainers/biobb_amber:4.2.0--pyhdfd78af_0",
    packages_to_install=[],
)
def run_minimization(
    input_top: Input[Artifact],
    input_crd: Input[Artifact],
    output_traj: Output[Artifact],
    output_rst: Output[Artifact],
    output_log: Output[Artifact],
    output_energy_dat: Output[Artifact],
):
    """Run AMBER Sander minimization with restraints on non-hydrogen atoms."""
    from biobb_amber.sander.sander_mdrun import sander_mdrun
    from biobb_amber.process.process_minout import process_minout
    import shutil
    import os

    # Copy input files from object storage to local paths
    local_top_path = "system.top"
    local_crd_path = "system.crd"

    shutil.copy(input_top.path, local_top_path)
    shutil.copy(input_crd.path, local_crd_path)
    print(f"Copied input files: TOP={local_top_path}, CRD={local_crd_path}")

    # Define local output paths
    local_traj_path = "sander.h_min.x"
    local_rst_path = "sander.h_min.rst"
    local_log_path = "sander.h_min.log"

    # Set up minimization parameters
    prop = {
        "simulation_type": "min_vacuo",
        "mdin": {
            "maxcyc": 500,
            "ntpr": 5,
            "ntr": 1,
            "restraintmask": '":*&!@H="',
            "restraint_wt": 50.0,
        },
    }

    # Run minimization
    print("Starting AMBER minimization...")
    sander_mdrun(
        input_top_path=local_top_path,
        input_crd_path=local_crd_path,
        input_ref_path=local_crd_path,  # Using input coords as reference
        output_traj_path=local_traj_path,
        output_rst_path=local_rst_path,
        output_log_path=local_log_path,
        properties=prop,
    )
    print("Minimization completed successfully")

    # Process minimization log to extract energies
    local_energy_dat_path = "sander.h_min.energy.dat"

    energy_prop = {"terms": ["ENERGY"]}

    # Process minimization output
    process_minout(
        input_log_path=local_log_path,
        output_dat_path=local_energy_dat_path,
        properties=energy_prop,
    )
    print("Energy data extraction completed")

    # Copy results to output artifacts
    #shutil.copy(local_traj_path, output_traj.path)
    shutil.copy(local_rst_path, output_rst.path)
    shutil.copy(local_log_path, output_log.path)
    shutil.copy(local_energy_dat_path, output_energy_dat.path)

    print("Minimization outputs:")
    print(f"  Trajectory: {output_traj.path}")
    print(f"  Restart: {output_rst.path}")
    print(f"  Log: {output_log.path}")
    print(f"  Energy data: {output_energy_dat.path}")

@component(
    base_image='quay.io/biocontainers/biobb_amber:4.2.0--pyhdfd78af_0',
    packages_to_install=[]
)
def run_system_minimization(input_top: Input[Artifact],
                          input_rst: Input[Artifact],  # Restart file from previous minimization
                          output_traj: Output[Artifact],
                          output_rst: Output[Artifact],
                          output_log: Output[Artifact],
                          output_energy_dat: Output[Artifact]):
    """Run second AMBER Sander minimization using restart from first minimization."""
    from biobb_amber.sander.sander_mdrun import sander_mdrun
    from biobb_amber.process.process_minout import process_minout
    import shutil
    import os
    
    # Copy input files from object storage to local paths
    local_top_path = "system.top"
    local_rst_path = "previous_min.rst"  # Restart file from previous minimization
    
    shutil.copy(input_top.path, local_top_path)
    shutil.copy(input_rst.path, local_rst_path)
    print(f"Copied input files: TOP={local_top_path}, RST={local_rst_path}")
    
    # Define local output paths
    local_traj_path = "sander.n_min.x"
    local_rst_path_out = "sander.n_min.rst"
    local_log_path = "sander.n_min.log"
    
    # Set up minimization parameters
    prop = {
        'simulation_type': "min_vacuo",
        "mdin": { 
            'maxcyc': 500,
            'ntpr': 5,
            'ntr': 1,
            'restraintmask': '\":*&!@H=\"',
            'restraint_wt': 50.0
        }
    }
    
    # Run minimization
    print("Starting system minimization...")
    sander_mdrun(input_top_path=local_top_path,
               input_crd_path=local_rst_path,  # Using restart from previous min
               input_ref_path=local_rst_path,  # Using restart from previous min as reference
               output_traj_path=local_traj_path,
               output_rst_path=local_rst_path_out,
               output_log_path=local_log_path,
               properties=prop)
    print("System minimization completed successfully")
    
    # Process minimization log to extract energies
    local_energy_dat_path = "sander.n_min.energy.dat"
    
    energy_prop = {
        "terms": ['ENERGY']
    }
    
    # Process minimization output
    process_minout(input_log_path=local_log_path,
                 output_dat_path=local_energy_dat_path,
                 properties=energy_prop)
    print("Energy data extraction completed")
    
    # Copy results to output artifacts
    #shutil.copy(local_traj_path, output_traj.path)
    shutil.copy(local_rst_path_out, output_rst.path)
    shutil.copy(local_log_path, output_log.path)
    shutil.copy(local_energy_dat_path, output_energy_dat.path)
    
    print("System minimization outputs:")
    print(f"  Trajectory: {output_traj.path}")
    print(f"  Restart: {output_rst.path}")
    print(f"  Log: {output_log.path}")
    print(f"  Energy data: {output_energy_dat.path}")


@pipeline(
    name="Molecular Dynamics Pipeline",
    description="Pipeline for setting up and running molecular dynamics simulations",
)
def md_pipeline(pdb_code: str = "1aki"):
    """Define the molecular dynamics pipeline."""

    # Download the PDB file
    download_task = download_pdb(pdb_code=pdb_code)

    # Prepare the PDB file for AMBER
    prepare_task = prepare_pdb(input_pdb_file=download_task.outputs["output_pdb_file"])

    # Create topology
    topology_task = create_topology(
        input_pdb=prepare_task.outputs["output_prepared_pdb"]
    )

    # Run minimization
    minimization_task = run_minimization(
        input_top=topology_task.outputs["output_top"],
        input_crd=topology_task.outputs["output_crd"]
    )

    # Run second minimization (system minimization)
    system_minimization_task = run_system_minimization(
        input_top=topology_task.outputs["output_top"],
        input_rst=minimization_task.outputs["output_rst"]
    )


# Use consistent file name
pipeline_file = os.path.join(parent_dir, "pipelines", "molecular_dynamics_pipeline.yaml")
compiler.Compiler().compile(md_pipeline, pipeline_file)


client = Client(host="http://localhost:8080")
run = client.create_run_from_pipeline_package(
    pipeline_file,
    arguments={
        "pdb_code": "1aki",
    },
)
# Get pipeline ID
pipeline_name = "Molecular Dynamics Pipeline"
# List all pipelines and find yours
all_pipelines = client.list_pipelines()
pipeline_id = None

if all_pipelines and all_pipelines.pipelines:
    for p in all_pipelines.pipelines:

        if p.display_name == "Molecular Dynamics Pipeline":
            pipeline_id = p.pipeline_id
            print(f"Found existing pipeline with ID: {pipeline_id}")
            break

if pipeline_id:
    # Upload a new version
    client.upload_pipeline_version(
        pipeline_package_path=pipeline_file,
        pipeline_version_name="1.0",
        description="Updated pipeline version",
        pipeline_id=pipeline_id
    )
else:
    # Pipeline doesn't exist, create it
    pipeline = client.upload_pipeline(
        pipeline_package_path=pipeline_file,
        pipeline_name="Molecular Dynamics Pipeline",
        description="Pipeline for setting up and running molecular dynamics simulations"
    )
    print(f"Created new pipeline with ID: {pipeline.pipeline_id}")

