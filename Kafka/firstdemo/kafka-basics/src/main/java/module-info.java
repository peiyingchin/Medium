module io.conduktor.demos.kafkabasics {
    requires javafx.controls;
    requires javafx.fxml;
    requires kafka.clients;


    opens io.conduktor.demos.kafkabasics to javafx.fxml;
    exports io.conduktor.demos.kafkabasics;
}