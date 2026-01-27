// src/resolvers/dto/otpResolverDto.ts
import { ArgsType, Field, ObjectType } from "type-graphql";
import { BaseResponse } from "./userResolverDto";

@ArgsType()
export class VerifyOtpArgs {
  @Field()
  email!: string;

  @Field()
  otp!: string;
// e.g., "signup_email_verification"
}
@ObjectType()
export class VerifyOtpResponse extends BaseResponse {}
