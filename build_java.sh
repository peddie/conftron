for class in `cat classes.dat`
do 
    jar cf java/${class}.jar java/${class}/*.class
done
