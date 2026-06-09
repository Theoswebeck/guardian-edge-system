read -p "Enter the location of the eSPD Laboratory repository [../eSPD-lab/]: " name
lab=${name:-../eSPD-lab/}

mkdir -p "$lab/datasets/"{VTPAN,PANC}

for dataset in PANC VTPAN; do
        for datasetType in train test; do
                echo "copying $dataset $datasetType"
                cp "$dataset/datapacks/datapack-$dataset-$datasetType.json" "$lab/datasets/$dataset/"
                cp "$dataset/csv/$dataset-$datasetType.csv" "$lab/datasets/$dataset/"
        done
done

