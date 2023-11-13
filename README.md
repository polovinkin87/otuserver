## Installation

Clone the repository from GitHub. Then create a virtual environment, and install all the dependencies.

```bash
git clone https://github.com/username/foobar.git
python3 -m venv env
source env/bin/activate
python -m pip install -r requirements.txt
```

## Usage

Initialize the virtual environment, and run the script

```bash
source env/bin/activate
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update the tests as appropriate.

## Load Testing

Results of load testing

```bash
ab -n 20000 -c 100 -r "http://localhost:8080/httptest/dir2"
This is ApacheBench, Version 2.3 <$Revision: 1879490 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking localhost (be patient)
Completed 2000 requests
Completed 4000 requests
Completed 6000 requests
Completed 8000 requests
Completed 10000 requests
Completed 12000 requests
Completed 14000 requests
Completed 16000 requests
Completed 18000 requests
Completed 20000 requests
Finished 20000 requests


Server Software:        HTTP
Server Hostname:        localhost
Server Port:            8080

Document Path:          /httptest/dir2
Document Length:        221 bytes

Concurrency Level:      100
Time taken for tests:   485.411 seconds
Complete requests:      20000
Failed requests:        700
   (Connect: 0, Receive: 234, Length: 233, Exceptions: 233)
Non-2xx responses:      19767
Total transferred:      7313790 bytes
HTML transferred:       4368507 bytes
Requests per second:    41.20 [#/sec] (mean)
Time per request:       2427.053 [ms] (mean)
Time per request:       24.271 [ms] (mean, across all concurrent requests)
Transfer rate:          14.71 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0  640 5435.8      0   65628
Processing:     0 1522 13704.8      4  131167
Waiting:        0   57 1237.7      3   54184
Total:          0 2161 14696.0      4  131167

Percentage of the requests served within a certain time (ms)
  50%      4
  66%      6
  75%      7
  80%      9
  90%     13
  95%   1011
  98%  31487
  99%  108443
 100%  131167 (longest request)
```