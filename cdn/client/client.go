package main

import (
	"bufio"
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"math/rand"
	"net"
	"net/http"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

const (
	delay   = 5 * time.Second
	timeout = 500 * time.Millisecond
	// timeout = 2500 * time.Millisecond
)

var (
	HOST        string
	lock        sync.Mutex
	keys        []string
	weights     []int
	totalWeight int
)

func init() {
	log.SetFlags(log.LstdFlags | log.Lshortfile | log.Lmicroseconds)
}

func readCSV(filename string) {
	data := make(map[string]int)

	file, err := os.Open(filename)
	if err != nil {
		log.Fatalf("Error opening file: %v", err)
	}
	defer file.Close()

	reader := csv.NewReader(bufio.NewReader(file))
	_, err = reader.Read() // skip header
	if err != nil {
		log.Fatalf("Error reading header: %v", err)
	}

	for {
		record, err := reader.Read()
		if err != nil {
			break
		}

		key := record[0] + record[1]
		value, _ := strconv.Atoi(record[3])
		data[key] = value
	}

	keys = make([]string, 0, len(data))
	weights = make([]int, 0, len(data))

	for k, v := range data {
		keys = append(keys, k)
		weights = append(weights, v)
	}

	totalWeight = 0
	for _, w := range weights {
		totalWeight += w
	}
}

var client = &http.Client{
	Timeout: timeout,
	Transport: &http.Transport{
		DialContext: (&net.Dialer{
			KeepAlive: 30 * time.Second,
		}).DialContext,
		MaxIdleConnsPerHost:   1000,
		MaxIdleConns:          1000,
		IdleConnTimeout:       90 * time.Second,
		TLSHandshakeTimeout:   10 * time.Second,
		ExpectContinueTimeout: 1 * time.Second,
	},
}

func makeReq(host string, key string) (float64, string, int, string) {
	req, err := http.NewRequest("GET", fmt.Sprintf("http://%s", host), strings.NewReader(key))
	// req, err := http.NewRequest("GET", "http://10.0.0.6:8000"+key, nil)
	if err != nil {
		log.Printf("Error creating request: %v", err)
		return 0, "Fail", 0, host
	}

	t1 := time.Now()
	resp, err := client.Do(req)
	t2 := time.Now()

	if err != nil {
		log.Printf("Error making request: %v", err)
		return 0, "Fail", 0, host
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		log.Printf("Error response: %v", resp.Status)
		return 0, "Fail", 0, host
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Printf("Error reading response: %v", err)
		return 0, "Fail", 0, host
	}

	response := string(body)
	hit := "False"
	if response != "" && response[len(response)-1] == '1' {
		hit = "True"
	}

	return t2.Sub(t1).Seconds(), hit, len(response), host
}

func updateServerPosition(orchestratorHost, clientName string) {
	conn, _, err := websocket.DefaultDialer.Dial(fmt.Sprintf("ws://%s", orchestratorHost), nil)

	if err != nil {
		log.Fatalf("Error connecting to orchestrator: %v", err)
	}
	defer conn.Close()

	log.Printf("Connected to orchestrator at %s", orchestratorHost)

	err = conn.WriteMessage(websocket.TextMessage, []byte(clientName))
	if err != nil {
		log.Fatalf("Error sending client name: %v", err)
	}

	log.Printf("Sent client name %s", clientName)

	for {
		t, message, err := conn.ReadMessage()

		if err != nil {
			log.Printf("Error receiving server position: %v", err)
			continue
		}

		if t != websocket.TextMessage {
			log.Printf("Received non-text message: %v (type %v)", message, t)
			continue
		}

		serverPosition := string(message)
		log.Printf("Received server position %s", serverPosition)

		if serverPosition == HOST {
			continue
		}

		lock.Lock()
		HOST = serverPosition
		log.Printf("Updated HOST to %s", HOST)
		lock.Unlock()
	}
}

func iperf() {
	for {
		lock.Lock()
		host := HOST
		lock.Unlock()

		if host == "" {
			time.Sleep(1 * time.Second)
			continue
		}

		host = strings.Split(host, ":")[0]

		cmd := exec.Command("iperf3", "-c", host)

		log.Printf("Running iperf command: %s", cmd)

		out, err := cmd.CombinedOutput()

		if err != nil {
			log.Printf("Error running iperf: %v", err)
		}

		log.Printf("iperf output: %s", out)

		<-time.After(10 * time.Second)
	}
}

func main() {
	if len(os.Args) < 3 {
		fmt.Printf("Usage: %s name orchestrator_host\n", os.Args[0])
		os.Exit(1)
	}

	name := os.Args[1]
	orchestratorHost := os.Args[2]

	// seed with name
	stringToInt64 := func(s string) int64 {
		var result int64 = 0
		for _, ch := range s {
			result = result*256 + int64(ch)
		}
		return result
	}

	rng := rand.New(rand.NewSource(stringToInt64(name)))

	readCSV("shortmedia.csv")

	go updateServerPosition(orchestratorHost, name)
	// go iperf()

	time.Sleep(time.Duration(rng.Float64()) * delay)

	randomKey := func() string {
		randWeight := rng.Intn(totalWeight)
		key := ""
		for i, w := range weights {
			if randWeight < w {
				key = keys[i]
				break
			}
			randWeight -= w
		}

		return key
	}

	NUM_CLIENTS := 1
	modDelay := delay / time.Duration(NUM_CLIENTS)
	ticker := time.NewTicker(modDelay)

	logSync := sync.Mutex{}

	for {
		<-ticker.C
		lock.Lock()
		var host string
		for {
			host = HOST
			if host != "" {
				break
			}
			lock.Unlock()
			log.Println("Waiting for connection")
			time.Sleep(1 * time.Second)
			lock.Lock()
		}

		go func() {
			key := randomKey()
			ts, cacheHit, resLen, host := makeReq(host, key)
			logSync.Lock()
			log.Printf("request_info: %s,%f,%s,%d,%s", key, ts, cacheHit, resLen, host)
			logSync.Unlock()
		}()
		lock.Unlock()
	}
}
