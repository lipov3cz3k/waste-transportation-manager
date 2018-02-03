# Use an official Python runtime as a parent image
FROM python:3.4

RUN apt-get update && apt-get install -y libboost-python-dev osmosis

WORKDIR /www/wtm
COPY ./src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src .

# Make port 80 available to the world outside this container
EXPOSE 5000

ENTRYPOINT ["python"]
# Run app.py when the container launches
CMD ["gui.py"]