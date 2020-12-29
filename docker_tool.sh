#!/usr/bin/env bash
while getopts ":h" opt; do
  case ${opt} in
    h )
      echo "Usage:"
      echo "    docker-tool.sh -h        Display this help message."
      echo "    docker-tool.sh build <VERSION>    Builds image"
      echo "    docker-tool.sh test <VERSION>    Tests image"
      echo "    docker-tool.sh publish <VERSION>  Publishes image to Docker Hub"
      echo "    docker-tool.sh latest <VERSION>  Tags images as latest on Docker Hub."
      echo "    docker-tool.sh run <VERSION>  Run the image locally"
      exit 0
      ;;
   \? )
     echo "Invalid Option: -$OPTARG" 1>&2
     exit 1
     ;;
  esac
done


test_docker_image() {
     docker run -d --name "$1" -p 5005:6006 -e HOST='0.0.0.0' berzemus/pyghotess:"$1"
     sleep 2
     url=http://localhost:5005/
     status=$(curl --get --location --connect-timeout 5 --write-out %{http_code} --silent --output /dev/null ${url})

     if [[ $status == '200' ]]
     then
      echo "$(tput setaf 2)Image: berzemus/pyghotess:${1} - Passed$(tput sgr0)"
      docker kill "$1"
      docker rm "$1"
     else
      echo "$(tput setaf 1)Image: berzemus/pyghotess:${1} - Failed$(tput sgr0)"
      docker kill "$1"
      docker rm "$1"
      exit 1
     fi
}

shift $((OPTIND -1))
subcommand=$1; shift
version=$1; shift

case "$subcommand" in
  build)
    # Build slim version with minimal dependencies
    docker build -t berzemus/pyghotess:${version}-api  -f ./Docker/Dockerfile_API --no-cache .
    #docker build -t berzemus/pyghotess:${version}-cli  -f ./Docker/Dockerfile_CLI --no-cache .
    ;;

  test)
    # Test the images
    test_docker_image ${version}-api
    # test_docker_image "${version}-cli"
    ;;

  publish)
    # Push the build images
    docker push berzemus/pyghotess:${version}-api
    # docker push berzemus/pyghotess:${version}-cli
    ;;

  latest)
    # Update the latest tags to point to supplied version
    docker tag berzemus/pyghotess:${version}-api berzemus/pyghotess:latest-api
    docker push berzemus/pyghotess:latest-api
    # docker tag berzemus/pyghotess:${version}-cli berzemus/pyghotess:latest-ocr
    # docker push berzemus/pyghotess:latest-ocr
    ;;

  run)
    # Run the image
    docker run -it --rm -p 6006:6006 berzemus/pyghotess:${version}-api
    ;;

esac
