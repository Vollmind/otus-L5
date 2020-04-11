# Scoring API

OTUS Python 2020-02 lession-5

## Purpose
File sender on sockets using threads

## Usage
Start server:
```bash
python httpd.py -p <port> -w <workers> -r <root_folder>
```

## Testing
Start unittests:
```bash
python -m unittest -v httptest
```

## Stress testing results
```
This is ApacheBench, Version 2.3 <$Revision: 1807734 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking localhost (be patient)
Completed 10000 requests
Completed 20000 requests
Completed 30000 requests
Completed 40000 requests
Completed 50000 requests
Completed 60000 requests
Completed 70000 requests
Completed 80000 requests
Completed 90000 requests
Completed 100000 requests
Finished 100000 requests


Server Software:        Python
Server Hostname:        localhost
Server Port:            8080

Document Path:          /httptest/dir2/
Document Length:        34 bytes

Concurrency Level:      500
Time taken for tests:   20.176 seconds
Complete requests:      100000
Failed requests:        0
Total transferred:      16300000 bytes
HTML transferred:       3400000 bytes
Requests per second:    4956.32 [#/sec] (mean)
Time per request:       100.881 [ms] (mean)
Time per request:       0.202 [ms] (mean, across all concurrent requests)
Transfer rate:          788.94 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   3.9      0    1014
Processing:    20  100  21.3     91     185
Waiting:       19  100  21.3     91     185
Total:         55  101  21.4     91    1121

Percentage of the requests served within a certain time (ms)
  50%     91
  66%     95
  75%    102
  80%    105
  90%    149
  95%    156
  98%    161
  99%    165
 100%   1121 (longest request)

```

## Author
Frantsev Matvey

12.04.2020