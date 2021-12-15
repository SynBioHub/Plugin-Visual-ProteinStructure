# Plugin-Visual-ProtienStructure
 A plugin for SynBioHub to visualize protein structures.

# Build the docker image
```
docker build -t plugin-visual-proteinstructure:0.1.0 . 
```

# Run the plugin as a standalone container
```
docker run --publish 8900:5000 --detach --name plugin-visual-proteinstructure plugin-visual-proteinstructure:0.1.0
```

# Test using Postman
Import the `Plugin-Visual-ProteinStructure.postman_collection.json` file into Postman, and run the tests by using the "Send" button. Click on the "Preview" tab in the response section to view rendered protein structure image.

# To deploy using docker-compose for use with SynBioHub
```
docker-compose -f docker-compose.pluginVisualProteinStructure.yml up -d
```