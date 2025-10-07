sudo docker run -it -d \
    --restart always \
    --runtime nvidia \
    --network host \
    --privileged \
    --device /dev/video0 \
    -v /tmp/argus_socket:/tmp/argus_socket \
    --env JETBOT_I2C_BUS=${JETBOT_I2C_BUS:-1} \
    --name=jetbot_display \
    $JETBOT_DOCKER_REMOTE/jetbot:display-$JETBOT_VERSION-$L4T_VERSION
