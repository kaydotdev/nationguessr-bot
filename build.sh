cargo build --release
cp target/release/nationguessr target/bootstrap
zip target/lambda.zip target/bootstrap
