import { ArgsType, Field, ObjectType } from "type-graphql";

@ObjectType()
export class BaseResponse {


  @Field(() => Boolean, { nullable: true })
  status?: boolean;

  @Field(() => Number, { nullable: true })
  code?: number;

  @Field(() => String, { nullable: true })
  message?: string;
}

@ArgsType()
export class SignupArgs {
  @Field()
  firstName!: string;

  @Field()
  lastName!: string;

  @Field(() => String, { nullable: false })
  username!: string;

  @Field(() => String, { nullable: false })
  email!: string;

  @Field(() => String, { nullable: false })
  password!: string; // Only passed to Clerk

  @Field()
  dob!: string; // YYYY-MM-DD

  @Field()
  phoneNumber!: string;
}



@ObjectType()
export class UserResponseDto {
  @Field(() => String)
  id!: string;

  @Field(() => String, { nullable: true })
  name?: string;

  @Field(() => String, { nullable: true })
  firstName?: string;

  @Field(() => String, { nullable: true })
  lastName?: string;

  @Field(() => String, { nullable: true })
  username?: string;

  @Field(() => String, { nullable: true })
  firebaseId?: string;

  @Field(() => String, { nullable: true })
  email?: string;

  @Field(() => String, { nullable: true })
  dob?: string;

  @Field(() => String, { nullable: true })
  phoneNumber?: string;

  @Field(() => Boolean, { nullable: true })
  isVerified?: boolean;
}

@ObjectType()
export class loginOrSignupWithGoogleResponseDto {
  @Field(() => String)
  firebaseToken!: string;
}


@ArgsType()
export class LoginArgs {
  @Field()
  email!: string;

  @Field()
  password!: string;
}


@ObjectType()
export class LoginResponseDto {
  @Field()
  idToken!: string;

  @Field({ nullable: true })
  refreshToken?: string;

  @Field({ nullable: true })
  expiresAt?: string;

  @Field({ nullable: true })
  userId?: string;

  @Field({ nullable: true })
  email?: string;
}


@ArgsType()
export class RefreshTokenArgs {
  @Field()
  refreshToken!: string;
}

@ObjectType()
export class RefreshTokenResponse {
  @Field()
  idToken!: string;

  @Field()
  refreshToken!: string;

  @Field()
  uid!: string;

  @Field({ nullable: true })
  email?: string;
}

@ArgsType()
export class SendPasswordResetEmailArgs {
  @Field()
  email!: string;
}

@ArgsType()
export class sendPasswordResetEmailResponse extends BaseResponse {
  @Field()
  email!: string;
}


@ArgsType()
export class GoogleSignupArgs {
  @Field()
  idToken!: string;

  @Field()
  dob!: string; // YYYY-MM-DD

  @Field()
  phoneNumber!: string;
}


@ArgsType()
export class VerifyTokenArgs {
  @Field()
  idToken!: string;
}

@ObjectType()
export class VerifyTokenResponse {
  @Field()
  uid!: string;

  @Field({ nullable: true })
  email?: string;
}


@ObjectType()
export class UserDetailsResponse extends BaseResponse {
  @Field(() => [UserResponseDto], { nullable: true })
  data?: UserResponseDto[]; // or single UserResponseDto
}

@ObjectType()
export class CreateUserResponseDto extends BaseResponse {
  @Field(() => UserResponseDto, { nullable: true })
  data?: UserResponseDto;
}

@ObjectType()
export class LoginResponse extends BaseResponse {
  @Field(() => LoginResponseDto, { nullable: true })
  data?: LoginResponseDto;
}

@ObjectType()
export class VerifyTokenFullResponse extends BaseResponse {
  @Field(() => VerifyTokenResponse, { nullable: true })
  data?: VerifyTokenResponse;
}

@ObjectType()
export class loginOrSignupWithGoogleResponse extends BaseResponse {
  @Field(() => loginOrSignupWithGoogleResponseDto, { nullable: true })
  data?: loginOrSignupWithGoogleResponseDto;
}

@ArgsType()
export class UpdateProfileInput {
  @Field(() => String, { nullable: true })
  firstName?: string;

  @Field(() => String, { nullable: true })
  lastName?: string;

  @Field(() => String, { nullable: true })
  dob?: string;

  @Field(() => String, { nullable: true })
  phoneNumber?: string;
}

@ArgsType()
export class FollowUserArgs {
  @Field()
  targetUserId!: string;
}