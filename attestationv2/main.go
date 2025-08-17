package main

import (
	"fmt"
	"os"
	"time"
)

func main() {
	f, err := os.Create(os.ExpandEnv("$HOME/hello-world.txt"))
	if err != nil {
		panic(err)
	}
	defer f.Close()

	for {
		timestamp := time.Now().Format(time.RFC3339)
		line := fmt.Sprintf("Hello World at %s\n", timestamp)
		f.WriteString(line)
		f.Sync()
		fmt.Println(line)
		time.Sleep(5 * time.Second)
	}
}
