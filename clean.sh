for class in `cat classes.dat`
do 
    rm ${class}/*.pyc;
    rm ${class}/*.py \
	&& rmdir ${class}; 
    rm ${class}.py
    rm ${class}.lcm
    rm ${class}_types.h
done

rm -f classes.dat
rm -f auto/*.c auto/*.h
rm -f telemetry/*.c telemetry/*.h
rm -f settings/*.c settings/*.h
rm -f airframes/*.h
rm -f stubs/*.c stubs/*.o
rm -f *_settings.h
rm -f *_telemetry.h *_telemetry.c
rm -f lcm_telemetry_auto.h lcm_settings_auto.h
rm -f *.a
