package main

import (
    "fmt"
    "io/ioutil"
    "os"
    "time"
)

func main() {
    fmt.Println("Hello from Go init!")

    filepath := "/testfile"
    content := []byte("hello world")

    // Write the file
    err := ioutil.WriteFile(filepath, content, 0644)
    if err != nil {
        fmt.Fprintf(os.Stderr, "Failed to write %s: %v\n", filepath, err)
    } else {
        fmt.Printf("File %s written successfully.\n", filepath)
    }

    // Check if file exists and read it
    if _, err := os.Stat(filepath); err == nil {
        data, _ := ioutil.ReadFile(filepath)
        fmt.Printf("Verified %s exists with content: %s\n", filepath, string(data))
    } else {
        fmt.Fprintf(os.Stderr, "File %s does not exist after write\n", filepath)
    }

    for {
        time.Sleep(1 * time.Hour)
    }
}