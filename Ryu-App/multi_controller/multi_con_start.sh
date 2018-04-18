
for i in $(seq 1 3)
    do 
    let port=i+5500
    xterm -title "app$i" -hold -e ryu-manager ryu.app.simple_switch_13.py --ofp-tcp-listen-port=$port &
    done
