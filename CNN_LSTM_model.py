import tensorflow as tf

# Define the CNN + LSTM hybrid model
def create_cnn_lstm_model(window_size=20, num_features=12):
    model = tf.keras.Sequential([
        tf.keras.layers.Conv1D(64, kernel_size=3, activation='relu', input_shape=(window_size, num_features)),
        tf.keras.layers.MaxPooling1D(pool_size=2),
        tf.keras.layers.Dropout(0.3),

        tf.keras.layers.LSTM(64),  # Long Short-Term Memory layer for sequence learning
        tf.keras.layers.Dropout(0.3),

        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dropout(0.3),

        tf.keras.layers.Dense(1, activation='sigmoid')  # Binary classification: 0 = healthy, 1 = impaired
    ])

    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy']
    )

    return model

# Example usage (untrained model)
if __name__ == "__main__":
    model = create_cnn_lstm_model()
    model.summary()  # Print architecture
    # Optional: save the untrained model
    model.save("cnn_lstm_untrained_model.h5")
    print("Model structure saved as cnn_lstm_untrained_model.h5")
