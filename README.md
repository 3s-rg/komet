# Komet: A Serverless Platform for Low-Earth Orbit Edge Services

tinyFaaS is a lightweight FaaS (Function-as-a-Service) platform for edge environment with a focus on performance in constrained environments.

This repository accompanies our paper **Komet: A Serverless Platform for Low-Earth Orbit Edge Services**.

If you use this software in a publication, please cite it as:

T. Pfandzelter and D. Bermbach, **Komet: A Serverless Platform for Low-Earth Orbit Edge Services**, Proceedings of the 15th ACM Symposium on Cloud Computing (SoCC '24), Redmond, WA, USA, 2024, DOI: 10.1145/3698038.3698517.

```bibtex
@inproceedings{pfandzelter2024komet,
    author = "Pfandzelter, Tobias and Bermbach, David",
    title = "Komet: A Serverless Platform for Low-Earth Orbit Edge Services",
    booktitle = "Proceedings of the 15th ACM Symposium on Cloud Computing",
    series = "SoCC '24",
    year = 2024,
    publisher = "Association for Computing Machinery (ACM)",
    doi = "10.1145/3698038.3698517"
}
```

For a full list of publications, please see [our website](https://www.tu.berlin/en/3s/research/publications).

## License

The code in this repository is licensed under the terms of the [MIT](./LICENSE) license.
There is some code taken from [Celestial](https://github.com/OpenFogStack), which is licensed under the terms of the [GPLv3](./scheduling/celestial/LICENSE) license (see the file heads, this only applies to the scheduling simulations).

## Usage

There is a separate directory for each experiment in our paper.
Each directory usually includes a Makefile to build the artifacts and an `experiment.sh` script to execute the experiment with given parameters.
In the root of this repository, there is another `experiment.sh` script that takes the desired experiment name (equals directory name) and host IP addresses or Google Cloud machine identifiers and executes the experiment.

| **Experiment**                     | **Directory**                    |
| ---------------------------------- | -------------------------------- |
| Container Migration (§3)           | [`containers`](./containers)     |
| Single Client Cache (§7.1)         | [`simple`](./simple)             |
| Single Client Cache Scaling (§7.1) | [`simple_scale`](./simple_scale) |
| Internet of Things (§7.2)          | [`iot`](./iot)                   |
| Content Delivery Network (§7.3)    | [`cdn`](./cdn)                   |
| Scheduling Simulations (§8)        | [`scheduling`](./scheduling)      |
