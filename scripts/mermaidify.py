import cppparser as cpp
import requests
import argparse
import os


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Mermaid diagrams from C++ classes of Entity"
    )
    parser.add_argument(
        "--branch",
        default="master",
        type=str,
        help="Git branch to use for fetching class definitions",
    )
    cwd = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument(
        "--output",
        default=os.path.join(cwd, "..", "docs", "assets", "diagrams"),
        type=str,
        help="Directory to save the generated Mermaid diagrams",
    )
    args = parser.parse_args()

    root_url = f"https://raw.githubusercontent.com/entity-toolkit/entity/refs/heads/{args.branch}/src"

    def get_class_from(file: str, which: int = 0) -> cpp.CPPClass:
        response = requests.get(f"{root_url}/{file}")
        if response.status_code != 200:
            raise FileNotFoundError(f"File {file} not found in branch {args.branch}")

        header = response.text
        parser = cpp.CPPParser(header)
        clss = parser.find_classes()
        return clss[which]

    domain = get_class_from("framework/domain/domain.h")
    metadomain = get_class_from("framework/domain/metadomain.h")
    mesh = get_class_from("framework/domain/mesh.h")
    grid = get_class_from("framework/domain/grid.h")

    species = get_class_from("framework/containers/species.h")
    particle_arrays = get_class_from("framework/containers/particles.h", 0)
    particles = get_class_from("framework/containers/particles.h", 1)
    fields = get_class_from("framework/containers/fields.h")

    metric = get_class_from("metrics/metric_base.h")
    metric_mink = get_class_from("metrics/minkowski.h")
    metric_sph = get_class_from("metrics/spherical.h")
    metric_qsph = get_class_from("metrics/qspherical.h")
    metric_ks = get_class_from("metrics/kerr_schild.h")
    metric_qks = get_class_from("metrics/qkerr_schild.h")
    metric_ks0 = get_class_from("metrics/kerr_schild_0.h")

    metadomain_short = metadomain.mermaid().split("\n")[0][:-1]
    domain_short = domain.mermaid().split("\n")[0][:-1]
    grid_short = grid.mermaid().split("\n")[0][:-1]
    mesh_short = mesh.mermaid().split("\n")[0][:-1]
    metric_short = metric.mermaid().split("\n")[0][:-1]
    species_short = species.mermaid().split("\n")[0][:-1]
    particle_arrays_short = particle_arrays.mermaid().split("\n")[0][:-1]
    particles_short = particles.mermaid().split("\n")[0][:-1]
    fields_short = fields.mermaid().split("\n")[0][:-1]

    notes = 'note "+: public\\n-: private\\n#: protected\\nunderline: static constexpr\\nitalic: virtual"'

    # Fields and Particles Diagram
    fields_particles_mmd = "classDiagram\n"
    fields_particles_mmd += f"  {domain_short}{{\n    see domain...*\n  }}\n"
    fields_particles_mmd += f"{species.mermaid(2)}\n"
    fields_particles_mmd += f"{particle_arrays.mermaid(2)}\n"
    fields_particles_mmd += f"{particles.mermaid(2)}\n"
    fields_particles_mmd += f"{fields.mermaid(2)}\n\n"

    fields_particles_mmd += "  Domain --* Particles : contains many\n"
    fields_particles_mmd += "  Domain --* Fields : contains\n"
    fields_particles_mmd += "  ParticleSpecies <|-- Particles : inherits\n\n"
    fields_particles_mmd += "  ParticleArrays <|-- Particles : inherits\n\n"

    fields_particles_mmd += f"  {notes}\n"

    # Domain Diagram
    domains_mmd = "classDiagram\n"
    domains_mmd += f"  {metric_short}{{\n    see metrics...*\n  }}\n"
    domains_mmd += f"  {fields_short}{{\n    see fields...*\n  }}\n"
    domains_mmd += f"  {particles_short}{{\n    see particles...*\n  }}\n"
    domains_mmd += f"{metadomain.mermaid(2)}\n"
    domains_mmd += f"{domain.mermaid(2)}\n"
    domains_mmd += f"{grid.mermaid(2)}\n"
    domains_mmd += f"{mesh.mermaid(2)}\n\n"

    domains_mmd += "  Domain --* Mesh : contains\n"
    domains_mmd += "  Grid <|-- Mesh : inherits\n"
    domains_mmd += "  Mesh --* MetricBase : contains\n"
    domains_mmd += "  Metadomain --* Domain : contains many\n"
    domains_mmd += "  Metadomain --* Mesh : contains\n"
    domains_mmd += "  Domain --* Fields : contains\n"
    domains_mmd += "  Domain --* Particles : contains many\n\n"

    domains_mmd += f"  {notes}\n"

    # Metrics Diagram
    metrics_mmd = "classDiagram\n"
    metrics_mmd += f"  direction LR\n"
    metrics_mmd += f"  {mesh_short}{{\n    see mesh...*\n  }}\n"
    metrics_mmd += f"{metric.mermaid(2)}\n\n"
    metrics_mmd += f"{metric_mink.mermaid(2)}\n"
    metrics_mmd += f"{metric_sph.mermaid(2)}\n"
    metrics_mmd += f"{metric_qsph.mermaid(2)}\n"
    metrics_mmd += f"{metric_ks.mermaid(2)}\n"
    metrics_mmd += f"{metric_qks.mermaid(2)}\n"
    metrics_mmd += f"{metric_ks0.mermaid(2)}\n\n"

    metrics_mmd += "  MetricBase <|-- Minkowski : implements\n"
    metrics_mmd += "  MetricBase <|-- Spherical : implements\n"
    metrics_mmd += "  MetricBase <|-- QSpherical : implements\n"
    metrics_mmd += "  MetricBase <|-- KerrSchild : implements\n"
    metrics_mmd += "  MetricBase <|-- QKerrSchild : implements\n"
    metrics_mmd += "  MetricBase <|-- KerrSchild0 : implements\n"
    metrics_mmd += "  Mesh --* MetricBase : contains\n\n"

    metrics_mmd += f"  {notes}\n"

    # Structures Diagram
    structures_mmd = "classDiagram\n"
    structures_mmd += f"  direction TB\n"
    structures_mmd += f"  {metadomain_short}{{\n    see metadomain...*\n  }}\n"
    structures_mmd += f"  {domain_short}{{\n    see domain...*\n  }}\n"
    structures_mmd += f"  {mesh_short}{{\n    see mesh...*\n  }}\n"
    structures_mmd += f"  {grid_short}{{\n    see grid...*\n  }}\n"
    structures_mmd += f"  {metric_short}{{\n    see metrics...*\n  }}\n"
    structures_mmd += f"  {species_short}{{\n    see species...*\n  }}\n"
    structures_mmd += (
        f"  {particle_arrays_short}{{\n    see particle arrays...*\n  }}\n"
    )
    structures_mmd += f"  {particles_short}{{\n    see particles...*\n  }}\n"
    structures_mmd += f"  {fields_short}{{\n    see fields...*\n  }}\n\n"

    structures_mmd += "  Domain --* Mesh : contains\n"
    structures_mmd += "  Grid <|-- Mesh : inherits\n"
    structures_mmd += "  Mesh --* MetricBase : contains\n"
    structures_mmd += "  Metadomain --* Domain : contains many\n"
    structures_mmd += "  Metadomain --* Mesh : contains\n"
    structures_mmd += "  Domain --* Fields : contains\n"
    structures_mmd += "  Domain --* Particles : contains many\n"
    structures_mmd += "  ParticleSpecies <|-- Particles : inherits\n"
    structures_mmd += "  ParticleArrays <|-- Particles : inherits\n"
    structures_mmd += "  Mesh --* MetricBase : contains\n\n"

    # Write to files
    with open(os.path.join(args.output, "fields-particles.mmd"), "w") as f:
        f.write(fields_particles_mmd)

    with open(os.path.join(args.output, "domains.mmd"), "w") as f:
        f.write(domains_mmd)

    with open(os.path.join(args.output, "metrics.mmd"), "w") as f:
        f.write(metrics_mmd)

    with open(os.path.join(args.output, "structures.mmd"), "w") as f:
        f.write(structures_mmd)
