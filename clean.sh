for class in `cat classes.dat`
do 
    rm ${class}.lcm
    rm ${class}_types.h
done

rm -f classes.dat &>/dev/null
rm -f auto/*.c auto/*.h &>/dev/null
rm -rf python/*
rm -f telemetry/*.c telemetry/*.h &>/dev/null
rm -f settings/*.c settings/*.h
rm -f airframes/*.h
rm -f stubs/*.c stubs/*.o
rm -f *_settings.h
rm -f *_telemetry.h *_telemetry.c &>/dev/null
rm -f lcm_telemetry_auto.h lcm_settings_auto.h
rm -f *.a *.o *~ *.s *.pyc &>/dev/null

