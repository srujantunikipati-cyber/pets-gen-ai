import admin from "firebase-admin";
import * as dotenv from "dotenv";
dotenv.config();


const serviceAccount = {
  type: "service_account",
  projectId: "petapp-11fa3",
  privateKeyId: "98c5f2d2f0b4700c987252c2d7bcf1a72e2b5f05",
  privateKey:  "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDI/D9TQ3dsnKIW\ns7F/y0eXDrJRlTlc7omb6CtYrlBzykutFILshyjfCWyPH6QFfzdAKri9crH9SXE/\nE9szYj0FSX1Go77WqB0qtDG+/qRzIWYxKFbPhYIuyHl39fU7OorD4f8EwnmVpw1m\n2F/Hwv8e5tjPpkc6aKm4I0DC+IbCoTdpoNawRh4tJ0nIrGGEIhp/S4II9+5HrpJt\nLvlwxVGJU4v3h3TYZeUOS3dN3JMbQ+pTZOCLvFb22xak4keKMrCBJB9w5LlG7nOD\n/T4ZEU61vCIk21orTR6vdm872Jw+/fgyg5XOivRvL3vArpViTZdlUZou7m9pEhZv\nC3H0FRuBAgMBAAECggEAAy1gVffMgK2u8zlCEB2NuZrntI0xytqaYBnyhb4R13Rc\nq5Dz4H9JS2t4STxnDCjulU0RMZOjB2uoXiasku6tI4qO1lWbvoyjm8yUtwIkQ5ZW\nFFXcjO2fnWS3dhFBBpC02s9q1K13B7jH+SfgC3tKtC7bDj8rcuQZR9KgLfcAbD2M\nylunc+RbMaVWeDTyK4meAQa/tESfdjtVmN54W07JW8Pg+7/REuJN7NXSmiHTjCos\nd4y4WUKx5ZVAnLYtpLq3kq/4dgrtZdW25WcaVPFdWxaliUaAp69wSRIF3iKAIPD+\nUtPIz+Un+6RYnlSCBYXHGiWr/FAwEp93eckWvmKaZwKBgQD8efTmskuj2VGsjPgO\n5bTYvjmfmFe0vpfiYrU5an9fEeDkeJQ+pCJE99UQGtrTvUyPXSzx9fqb8BgtQDEF\nNeP0Gze6QKA7nQxqyC7LGREz1+Q2q6GwGCPOO0emGYXXpCsgBtdWm+rddsvy3tuX\nhe3yPB4SY2S1NTmuhQE0WeNm+wKBgQDLylMJrcCWLtYWjgIhfe/P8Gifz3RqWSUH\nUILBKIsE1njNn8foEnd/MH6hZLL4UzAF7AQ/gW0rFPDXAHS/gaScCzyOy9m4Aywb\nHx94x2yptULqJnaOzoDNRKflBnVtm7livLESbdAQlEQ0VOYOAVKqn7T1qn/jXboF\nil+BoEkuswKBgC2kvqmWQiZ0+1b+hTnsPS2R9kjr+a8rZbn/rlOa9Tvyt32WbvaE\nJc3iIBqxQC5XYqfoaF+14ICgfz5vBG20uGlBImoBlPYyBjSnzA3bkkiVFyTrEmgL\ndS2reeCFbLT3cPRxSCzYMzWmbGiT8Y8LH2FTjPw2C9bWsH7kfLtCJOJRAoGACX2G\nmHDLAzNzLOG4H68pt9lORgL3POyh2NFbBXvJ3ZPPVGQYfyo8/mNXwlRaMU5Ocjgn\nin2Qg+0Zuil/RlvXOp0bWNsNbJBZQXoVkR5YZR7X2uenpcbgIK8N0pCWb2BNJdf7\ntwv+IIeHFZjOjeBp5SBC4R3rjr8SpqdnAzZfshkCgYEA6wA8IfVvwq1tcsvOIQp4\nEjOKjblunQjUfcTeLo6y2Hprff9HSAKBbC351/GDrfxEUgjnbUIdAad4TN7pX08O\nEGsdE4DyXu7Xh24jqCts6ypn+OqPcqoxMFt1AVpXY9wEPgCZVYJcjfv4lUseSiOT\n5l5m2eFzCv06DUf5+8AG7I4=\n-----END PRIVATE KEY-----\n",
  clientEmail: "firebase-adminsdk-fbsvc@petapp-11fa3.iam.gserviceaccount.com",
  clientId: "113760564097649204419",
  authUri: "https://accounts.google.com/o/oauth2/auth",
  tokenUri: "https://oauth2.googleapis.com/token",
  authProviderX509CertUrl: "https://www.googleapis.com/oauth2/v1/certs",
  clientX509CertUrl: "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40petapp-11fa3.iam.gserviceaccount.com",
  universeDomain: "googleapis.com"
};



// const serviceAccount = {
//   type: "service_account",
//   project_id: "petapp-11fa3",
//   private_key_id: "98c5f2d2f0b4700c987252c2d7bcf1a72e2b5f05",
//   private_key: "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDI/D9TQ3dsnKIW\ns7F/y0eXDrJRlTlc7omb6CtYrlBzykutFILshyjfCWyPH6QFfzdAKri9crH9SXE/\nE9szYj0FSX1Go77WqB0qtDG+/qRzIWYxKFbPhYIuyHl39fU7OorD4f8EwnmVpw1m\n2F/Hwv8e5tjPpkc6aKm4I0DC+IbCoTdpoNawRh4tJ0nIrGGEIhp/S4II9+5HrpJt\nLvlwxVGJU4v3h3TYZeUOS3dN3JMbQ+pTZOCLvFb22xak4keKMrCBJB9w5LlG7nOD\n/T4ZEU61vCIk21orTR6vdm872Jw+/fgyg5XOivRvL3vArpViTZdlUZou7m9pEhZv\nC3H0FRuBAgMBAAECggEAAy1gVffMgK2u8zlCEB2NuZrntI0xytqaYBnyhb4R13Rc\nq5Dz4H9JS2t4STxnDCjulU0RMZOjB2uoXiasku6tI4qO1lWbvoyjm8yUtwIkQ5ZW\nFFXcjO2fnWS3dhFBBpC02s9q1K13B7jH+SfgC3tKtC7bDj8rcuQZR9KgLfcAbD2M\nylunc+RbMaVWeDTyK4meAQa/tESfdjtVmN54W07JW8Pg+7/REuJN7NXSmiHTjCos\nd4y4WUKx5ZVAnLYtpLq3kq/4dgrtZdW25WcaVPFdWxaliUaAp69wSRIF3iKAIPD+\nUtPIz+Un+6RYnlSCBYXHGiWr/FAwEp93eckWvmKaZwKBgQD8efTmskuj2VGsjPgO\n5bTYvjmfmFe0vpfiYrU5an9fEeDkeJQ+pCJE99UQGtrTvUyPXSzx9fqb8BgtQDEF\nNeP0Gze6QKA7nQxqyC7LGREz1+Q2q6GwGCPOO0emGYXXpCsgBtdWm+rddsvy3tuX\nhe3yPB4SY2S1NTmuhQE0WeNm+wKBgQDLylMJrcCWLtYWjgIhfe/P8Gifz3RqWSUH\nUILBKIsE1njNn8foEnd/MH6hZLL4UzAF7AQ/gW0rFPDXAHS/gaScCzyOy9m4Aywb\nHx94x2yptULqJnaOzoDNRKflBnVtm7livLESbdAQlEQ0VOYOAVKqn7T1qn/jXboF\nil+BoEkuswKBgC2kvqmWQiZ0+1b+hTnsPS2R9kjr+a8rZbn/rlOa9Tvyt32WbvaE\nJc3iIBqxQC5XYqfoaF+14ICgfz5vBG20uGlBImoBlPYyBjSnzA3bkkiVFyTrEmgL\ndS2reeCFbLT3cPRxSCzYMzWmbGiT8Y8LH2FTjPw2C9bWsH7kfLtCJOJRAoGACX2G\nmHDLAzNzLOG4H68pt9lORgL3POyh2NFbBXvJ3ZPPVGQYfyo8/mNXwlRaMU5Ocjgn\nin2Qg+0Zuil/RlvXOp0bWNsNbJBZQXoVkR5YZR7X2uenpcbgIK8N0pCWb2BNJdf7\ntwv+IIeHFZjOjeBp5SBC4R3rjr8SpqdnAzZfshkCgYEA6wA8IfVvwq1tcsvOIQp4\nEjOKjblunQjUfcTeLo6y2Hprff9HSAKBbC351/GDrfxEUgjnbUIdAad4TN7pX08O\nEGsdE4DyXu7Xh24jqCts6ypn+OqPcqoxMFt1AVpXY9wEPgCZVYJcjfv4lUseSiOT\n5l5m2eFzCv06DUf5+8AG7I4=\n-----END PRIVATE KEY-----\n",
//   client_email: "firebase-adminsdk-fbsvc@petapp-11fa3.iam.gserviceaccount.com",
//   client_id: "113760564097649204419",
//   auth_uri: "https://accounts.google.com/o/oauth2/auth",
//   token_uri: "https://oauth2.googleapis.com/token",
//   auth_provider_x509_cert_url: "https://www.googleapis.com/oauth2/v1/certs",
//   clientX509CertUrl: "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40petapp-11fa3.iam.gserviceaccount.com",
//   universe_domain: "googleapis.com"
// }


admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
});

export default admin;
