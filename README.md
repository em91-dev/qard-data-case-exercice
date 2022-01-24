This is a prototype of solution for the exercice [https://github.com/ierpDesbieres/qard-data-case]

**General remarks**
   * The names can be written with different forms, can be abbreviated, inversed (first name / last name), have errors, etc.
   * Sometimes there are title(s) before the name that could help (Monsieur, Madames, Maître, président, etc.)
   * Here, the language is the French, the names can be from different origins however

**Environment and code**

   The exercice is run in a docker environment; the main files and directories:
   * **Dockerfile** is used to build an Ubuntu image with the necessary packages
   * **src/app.py** is the source of the program
   * **docker_run.sh** is the script that executes the program in Docker.
   * **qard-data-base/** is a copy of the github exercice (**clone.sh**)
   * **db/** contains some read-only database downloaded from internet
   * **out/result.json** is the result of the program in JSON format  


   Several methods are applied to try to extract the names from the texts:
   * method based on regular expressions
   * method using a database of firstname [https://www.data.gouv.fr/fr/datasets/liste-de-prenoms]
   * method based on the Spacy tagger  


   A final decision method is applied on the output of the previous methods (vote by majority).
 
**Few ideas to go further**
   * Set up some test framework to validate the results
   * Studying and including other methods to extract names (neural networks, nlp systems, etc.)
   * Improving the combination method
   * Optimization of the execution time for large set of data
 
