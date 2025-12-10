pipeline {
    agent any

    environment {
        AWS_DEFAULT_REGION = 'ap-south-1'
        S3_BUCKET          = 'hardik-aws-exam-bucket'
        LAMBDA_FUNCTION    = 'EmployeeApiFunction'
        ZIP_FILE           = 'lambda_package.zip'
    }

    stages {
        stage('Checkout') {
            steps {
                // Jenkins will use the repo configured in the job
                checkout scm
            }
        }

        stage('Prepare Workspace') {
            steps {
                sh 'rm -rf build || true'
                sh 'mkdir -p build'
                // Clean up previous zip file if exists
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    if [ -f requirements.txt ]; then
                        python3 -m pip install -r requirements.txt -t build/
                    fi
                '''
            }
        }

        stage('Copy Source') {
            steps {
                sh '''
                    cp lambda_function.py build/
                '''
            }
        }

        stage('Package Lambda') {
            steps {
                dir('build') {
                    sh 'zip -r ../${ZIP_FILE} .'
                }
            }
        }

        stage('Upload to S3') {
            steps {
                withAWS(credentials: 'aws-creds', region: "${AWS_DEFAULT_REGION}") {
                    sh 'aws s3 cp ${ZIP_FILE} s3://${S3_BUCKET}/${ZIP_FILE}'
                }
            }
        }

        stage('Deploy Lambda') {
            steps {
                withAWS(credentials: 'aws-creds', region: "${AWS_DEFAULT_REGION}") {
                    sh '''
                        set -e

                        if aws lambda get-function --function-name "${LAMBDA_FUNCTION}" > /dev/null 2>&1; then
                          echo "Lambda function exists, updating code..."
                          aws lambda update-function-code \
                            --function-name "${LAMBDA_FUNCTION}" \
                            --s3-bucket "${S3_BUCKET}" \
                            --s3-key "${ZIP_FILE}"
                        else
                          echo "Lambda function does not exist, creating..."
                          # NOTE: Role ARN must match the one from CloudFormation
                          ROLE_ARN=$(aws iam get-role --role-name EmpMasterLambdaExecutionRole --query "Role.Arn" --output text)

                          aws lambda create-function \
                            --function-name "${LAMBDA_FUNCTION}" \
                            --runtime python3.12 \
                            --handler lambda_function.lambda_handler \
                            --role "${ROLE_ARN}" \
                            --code S3Bucket="${S3_BUCKET}",S3Key="${ZIP_FILE}" \
                            --timeout 10 \
                            --environment "Variables={TABLE_NAME=Emp_Master}"
                        fi
                    '''
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: "${ZIP_FILE}", fingerprint: true
        }
    }
}
